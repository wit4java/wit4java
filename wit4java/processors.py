"""
 This file is part of wit4java, an execution-based violation-witness validator for Java
 https://github.com/wit4java/wit4java.

 This module deals with the processing of the witness, benchmark and packages
"""

from abc import ABC, abstractmethod
import re
from distutils.dir_util import copy_tree
import os
import networkx as nx


class Processor(ABC):
    """
    An abstract class representing the base functionality for a processor
    """

    def __init__(self, working_dir):
        self.working_dir = working_dir

    @abstractmethod
    def preprocess(self):
        """
        Stub for the preprocess method
        """

    def write_to_working_dir(self, path, data):
        """
        Writes some data to the working directory at some given path offset
        :param path: The offset path from the working directory
        :param data: The data to be written
        :return: The new place the data was written to.
        """
        # Check if incoming path involves a new subdirectory
        subdir = os.path.join(self.working_dir, os.path.dirname(path))
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        new_path = os.path.join(self.working_dir, path)
        with open(new_path, 'w', encoding='utf-8') as file:
            file.write(data)

        return new_path


class WitnessProcessor(Processor):
    """
    A class representing the witness processor
    """

    def __init__(self, working_dir, witness_path):
        super().__init__(working_dir)
        self.producer = None
        self.witness_path = witness_path

    def preprocess(self) -> None:
        """
        Preprocess the witness to avoid any unformatted XML
        """
        with open(self.witness_path, 'r', encoding='utf-8') as file:
            data = file.read()
        # Check for malformed XML strings
        cleaned_data = re.sub(r"\(\"(.*)<(.*)>(.*)\"\)", r'("\1&lt;\2&gt;\3")', data)
        if cleaned_data != data:
            path = "cleaned_witness.grapmhl"
            self.witness_path = self.write_to_working_dir(path, cleaned_data)

    @staticmethod
    def _extract_value_from_assumption(assumption, regex):
        """
        Extracts an assumption value using a regex
        :param assumption: The string containing the variable assignment to have value extracted
        :param regex: The regular expression used to extract the value
        :return: The extracted assumption value or None if not there
        """
        search_result = re.search(regex, assumption)
        if search_result is not None:
            matches = [sr for sr in search_result.groups() if sr is not None]
            # Match the last capture group if multiple matches
            assumption_value = matches[-1]
        else:
            # Check to see if it is because nondet comes from a function return
            # and in which case it is not assigned to a variable so remove = match from regex
            regex = regex[2:]
            search_result = re.search(regex, assumption)
            if search_result is not None:
                matches = [sr for sr in search_result.groups() if sr is not None]
                # Match the last capture group if multiple matches
                assumption_value = matches[-1]
            else:
                assumption_value = None

        return assumption_value

    def extract_assumptions(self):
        """
        Extracts the assumptions from the witness
        """
        try:
            witness_file = nx.read_graphml(self.witness_path)
        except Exception as exc:
            raise ValueError('Witness file is not formatted correctly.') from exc

        self.producer = witness_file.graph["producer"] if "producer" in witness_file.graph else None
        assumptions = []
        # GDart uses different syntax for numeric types
        if self.producer == "GDart":
            regex = r"= (-?\d*\.?\d+|false|true)|\w+\.equals\(\"(.*)\"\)|\w+\.parseDouble\(\"(" \
                    r".*)\"\)|\w+\.parseFloat\(\"(.*)\"\)"
        else:
            regex = r"= (-?\d*\.?\d+|false|true|null)\W"
        for assumption_edge in filter(
                lambda edge: ("assumption.scope" in edge[2]),
                witness_file.edges(data=True)
        ):
            data = assumption_edge[2]
            program = data["originFileName"]
            file_name = program[program.rfind("/") + 1: program.find(".java")]
            scope = data["assumption.scope"]
            if file_name not in scope:
                continue
            assumption = data["assumption"]
            assumption_value = self._extract_value_from_assumption(assumption, regex)
            if assumption_value is not None:
                if self.producer != "GDart" and assumption_value == "null":
                    assumption_value = None
                assumptions.append(assumption_value)
        return assumptions


class JavaFileProcessor(Processor):
    """
    A class representing the java files processor
    """
    def __init__(self, working_dir, benchmark_path, package_paths):
        super().__init__(working_dir)
        self.benchmark_path = benchmark_path
        self.package_paths = package_paths

    def preprocess(self):
        copy_tree(self.benchmark_path, self.working_dir)
        for package in self.package_paths:
            copy_tree(package, self.working_dir)
