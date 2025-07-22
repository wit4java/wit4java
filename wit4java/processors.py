"""
 This file is part of wit4java, an execution-based violation-witness validator for Java
 https://github.com/wit4java/wit4java.

 This module deals with the processing of the witness, benchmark and packages
"""

import glob
from abc import ABC, abstractmethod
import re
from distutils.dir_util import copy_tree
import os
import networkx as nx
import javalang


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
        with open(new_path, "w", encoding="utf-8") as file:
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
        with open(self.witness_path, "r", encoding="utf-8") as file:
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
        # Strip trailing semi colon if has been missed by regex
        if assumption_value.endswith(";"):
            assumption_value = assumption_value[:-1]
        # TODO Extract into new parser class and have methods handling specific edge values
        if assumption_value == "Double.NaN":
            assumption_value = "NaN"
        return assumption_value

    def extract_assumptions(self):
        """
        Extracts the assumptions from the witness
        """
        try:
            witness_file = nx.read_graphml(self.witness_path)
        except Exception as exc:
            raise ValueError("Witness file is not formatted correctly.") from exc

        self.producer = (
            witness_file.graph["producer"] if "producer" in witness_file.graph else None
        )
        assumptions = []
        # Should not bias for GDart in SVCOMP.
        # if self.producer == 'GDart':
        #     regex = r"= (-?\d*\.?\d+|false|true)|\w+\.equals\(\"(.*)\"\)|\w+\.parseDouble\(\"(" \
        #             r".*)\"\)|\w+\.parseFloat\(\"(.*)\"\)"
        # else:
        #     regex = r"= ((\S+)|(-?\d*\.?\d+[L]?)|(false|true|null))"
        regex = r"= (-?\d*\.?\d+[L]?|false|true|null|\S+)|\w+\.equals\(\"(.*)\"\)|\w+\.parseDouble\(\"(.*)\"\)|\w+\.parseFloat\(\"(.*)\"\)"
        for assumption_edge in filter(
            lambda edge: ("assumption.scope" in edge[2]), witness_file.edges(data=True)
        ):
            data = assumption_edge[2]
            program = data["originFileName"]
            file_name = program[program.rfind("/") + 1 : program.find(".java")]
            scope = data["assumption.scope"]
            if file_name not in scope:
                continue
            assumption_value = self._extract_value_from_assumption(
                data["assumption"], regex
            )
            if assumption_value is not None:
                if self.producer != "GDart" and assumption_value == "null":
                    assumption_value = None
                assumptions.append(((file_name, data["startline"]), assumption_value))
        return assumptions


class JavaFileProcessor(Processor):
    """
    A class representing the java files processor
    """

    def __init__(self, working_dir, benchmark_path, package_paths):
        super().__init__(working_dir)
        self.benchmark_path = benchmark_path
        self.package_paths = package_paths
        self.source_files = [
            f for f in glob.glob(self.benchmark_path + "/**/*.java", recursive=True)
        ]

    def preprocess(self):
        copy_tree(self.benchmark_path, self.working_dir)
        for package in self.package_paths:
            copy_tree(package, self.working_dir)

    def _check_valid_import(self, import_line):
        check_file = (
            import_line.strip()
            .replace(".", "/")
            .replace(";", "")
            .replace("import", "")
            .replace(" ", "")
        )
        if not check_file.startswith("java"):
            # Check in working directory
            files_exists = [
                source_f.endswith("{0}.java".format(check_file))
                for source_f in self.source_files
            ]
            if sum(files_exists) > 1:
                raise ValueError("Multiple classes for {0} given.".format(check_file))
            if sum(files_exists) == 1:
                # Return full path of the only existing file definition
                return [self.source_files[files_exists.index(True)]]

            # Check in packages
            # Check for wildcard imports
            if check_file.endswith("/*"):
                wildcard_import = check_file.replace("/*", "")
                dir_exists = [p.endswith(wildcard_import) for p in self.package_paths]
                if sum(dir_exists) == 1:
                    package = self.package_paths[dir_exists.index(True)]
                    return [
                        f for f in glob.glob(package + "/**/*.java", recursive=True)
                    ]

            full_paths = [
                "{0}.java".format(os.path.join(dir, check_file))
                for dir in self.package_paths
            ]
            files_exists = [os.path.exists(f_path) for f_path in full_paths]
            # Check there is only one definition for an import file and if so add to stack to check
            # for possible nondet calls
            if not any(files_exists):
                raise ValueError(
                    "No class for {0} given in classpath.".format(check_file)
                )
            elif sum(files_exists) > 1:
                raise ValueError(
                    "Multiple classes for {0} given in classpath.".format(check_file)
                )
            else:
                # Return full path of the only existing file definition
                return [full_paths[files_exists.index(True)]]
        return []

    def extract_nondet_mappings(self):
        types_map = {}
        nondet_functions_map = {}
        extraction_stack = dict.fromkeys(self.source_files, 0)
        finished_set = {}

        while len(extraction_stack) > 0:
            filename, _ = extraction_stack.popitem()
            finished_set[filename] = 0
            program_name = filename[filename.rfind("/") + 1 : filename.find(".java")]
            with open(filename, "r", encoding="utf-8") as file:
                data = file.read()
            # Dont need to check the Verifier class
            # TODO: Change Tool definition to not pass it
            if program_name == "Verifier":
                continue
            try:
                tree = javalang.parse.parse(data)
            except javalang.parser.JavaSyntaxError as err:
                print(err)
                tree = []
            for import_node in tree.imports:
                files = self._check_valid_import(import_node.path)
                for file in files:
                    if (
                        file is not None
                        and file not in extraction_stack
                        and file not in finished_set
                    ):
                        extraction_stack[file] = 0
            # Look for nondet Calls
            for _, node in tree.filter(javalang.tree.MethodInvocation):
                if (
                    node is not None
                    and node.qualifier is not None
                    and "Verifier" in node.qualifier
                ):
                    nondet_type = node.member.replace("nondet", "")
                    types_map[(program_name, node.position.line)] = nondet_type.lower()
            # Check if any nondet calls are from returns from methods
            for _, node in tree.filter(javalang.tree.MethodDeclaration):
                if node.body is None or len(node.body) == 0:
                    continue
                statement = node.body[0]
                if (
                    type(statement) == javalang.tree.ReturnStatement
                    and (program_name, statement.position.line) in types_map
                ):
                    nondet_functions_map[node.name] = (
                        program_name,
                        statement.position.line,
                    )

            # Add any nondet returning functions to list of nondet function calls
            for _, node in tree.filter(javalang.tree.MethodInvocation):
                if node is not None and node.member in nondet_functions_map:
                    position = nondet_functions_map[node.member]
                    types_map[(program_name, node.position.line)] = types_map[position]

        return types_map


def filter_assumptions(nondet_mappings, assumptions_list):
    """
    Filters assumptions to only contain values from nondet function calls.
    :param nondet_mappings: A mapping from a position of a nondet call to its type
    :param assumptions_list: A list of assumptions
    :return: A list of assumptions values that come from nondet functions
    """
    filtered_assumptions = filter(
        lambda assumption: (assumption[0] in nondet_mappings), assumptions_list
    )
    return list(map(lambda assumption: assumption[1], filtered_assumptions))
