import sys
from abc import ABC, abstractmethod
import glob
import re
import networkx as nx
import os
from distutils.dir_util import copy_tree


class Processor(ABC):
    """
    An abstract class representing the base functionality for a processor
    """
    def __init__(self, working_dir):
        self.working_dir = working_dir

    @abstractmethod
    def preprocess(self):
        pass

    @abstractmethod
    def extract(self):
        pass

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
        with open(new_path, 'w') as file:
            file.write(data)

        return new_path


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


class WitnessProcessor(Processor):
    """
    A class representing the witness processor
    """
    def __init__(self, working_dir, witness_path):
        super().__init__(working_dir)
        self.producer = None
        self.witness_path = witness_path

    def preprocess(self):
        """

        """
        with open(self.witness_path, 'r') as file:
            data = file.read()
        # Check for malformed XML strings
        cleaned_data = re.sub(r"\(\"(.*)<(.*)>(.*)\"\)", r'("\1&lt;\2&gt;\3")', data)
        if cleaned_data != data:
            path = "cleaned_witness.grapmhl"
            self.witness_path = self.write_to_working_dir(path, cleaned_data)

    def extract(self):
        """

        """
        try:
            witness_file = nx.read_graphml(self.witness_path)
        except Exception:
            raise ValueError('Witness file is not formatted correctly.')

        self.producer = witness_file.graph["producer"] if "producer" in witness_file.graph else None
        assumptions = []
        # GDart uses different syntax for numeric types
        if self.producer == "GDart":
            regex = r"= (-?\d*\.?\d+|false|true)|\w+\.equals\(\"(.*)\"\)|\w+\.parseDouble\(\"(.*)\"\)|\w+\.parseFloat\(\"(.*)\"\)"
        else:
            regex = r"= (-?\d*\.?\d+|false|true|null)\W"

        for assump_edge in filter(lambda edge: ("assumption.scope" in edge[2]), witness_file.edges(data=True)):
            data = assump_edge[2]
            program = data["originFileName"]
            file_name = program[program.rfind("/") + 1: program.find(".java")]
            scope = data["assumption.scope"]
            if file_name not in scope:
                continue
            assumption = data["assumption"]
            start_line = data["startline"]
            assumption_value = _extract_value_from_assumption(assumption, regex)
            if assumption_value is not None:
                if self.producer != "GDart" and assumption_value == "null":
                    assumption_value = None
                assumptions.append(((file_name, start_line), assumption_value))
        return assumptions


def _find_between(s, start, end):
    return (s.split(start))[1].split(end)[0]


class JavaFileProcessor(Processor):
    def __init__(self, working_dir, benchmark_path, package_paths):
        super().__init__(working_dir)
        self.benchmark_path = benchmark_path
        self.source_files = [f for f in glob.glob(self.benchmark_path + "/**/*.java", recursive=True)]
        self.package_paths = package_paths

    def preprocess(self):
        copy_tree(self.benchmark_path, self.working_dir)

    def _check_valid_import(self, import_line):
        check_file = import_line.strip().replace(".", "/").replace(";", "").replace("import", "").replace(' ', '')
        if not check_file.startswith('java'):
            # Check in working directory
            files_exists = [source_f.endswith("{0}.java".format(check_file)) for source_f in self.source_files]
            if sum(files_exists) > 1:
                raise ValueError('Multiple classes for {0} given.'.format(check_file))
            elif sum(files_exists) == 1:
                # Return full path of the only existing file definition
                return self.source_files[files_exists.index(True)]

            # Check in packages
            full_paths = ["{0}.java".format(os.path.join(dir, check_file)) for dir in self.package_paths]
            files_exists = [os.path.exists(f_path) for f_path in full_paths]
            # Check there is only one definition for an import file and if so add to stack to check
            # for possible nondet calls
            if not any(files_exists):
                raise ValueError('No class for {0} given in classpath.'.format(check_file))
            elif sum(files_exists) > 1:
                raise ValueError('Multiple classes for {0} given in classpath.'.format(check_file))
            else:
                # Return full path of the only existing file definition
                return full_paths[files_exists.index(True)]
        return None

    def extract(self):
        types_map = {}
        extraction_stack = dict.fromkeys(self.source_files, 0)
        while len(extraction_stack) > 0:
            filename, _ = extraction_stack.popitem()
            program_name = filename[filename.rfind("/") + 1: filename.find(".java")]
            with open(filename, "r") as f:
                for line_number, line in enumerate(f, 1):
                    if line.strip().startswith('import'):
                        file = self._check_valid_import(line)
                        if file is not None and file not in extraction_stack:
                            extraction_stack[file] = 0

                    search_string = "Verifier.nondet"
                    if search_string in line:
                        type = _find_between(line, "nondet", "(")
                        types_map[(program_name, line_number)] = type.lower()
        return types_map


def construct_type_assumption_pairs(file_line_type_map, assumptions_list):
    # Get all assumption positions
    assumptions_position_list = [assumption_position for (assumption_position, _) in assumptions_list]
    # Check each nondet call has greater than one assumption
    if not all(position in assumptions_position_list for position in file_line_type_map.keys()):
        raise ValueError('Not all nondet calls have been assigned assumptions, cannot verify.')
    # Map each assumption to its respective
    type_assumption_pairs = [(file_line_type_map[position], value) for (position, value) in assumptions_list
                             if position in file_line_type_map]
    return type_assumption_pairs