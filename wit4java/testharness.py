"""
 This file is part of wit4java, an execution-based violation-witness validator for Java
 https://github.com/wit4java/wit4java.

 This module deals with the building of the testing .java files
"""

import os
import subprocess
from typing import List, Tuple


class TestHarness:
    """
    The class TestBuilder manages all the tests creation and compilation
    of the tests harness
    """

    VERIFIER_PACKAGE = "org/sosy_lab/sv_benchmarks"
    VERIFIER_RESOURCE_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "resources/Verifier.java"
    )
    TEST_RESOURCE_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "resources/Test.java"
    )

    def __init__(self, directory):
        """
        The constructor of TestBuilder collects information on the output directory
        :param directory: Directory that the harness will write to
        """
        self.directory = directory
        self.verifier_path = os.path.join(
            self.directory, f"{self.VERIFIER_PACKAGE}/Verifier.java"
        )
        self.test_path = os.path.join(self.directory, "Test.java")

    @staticmethod
    def _read_data(path: str) -> List[str]:
        """
        Handles reading data from a file
        :param path: Path of a file to read from
        :return: Content of file
        """
        with open(path, "r", encoding="utf-8") as file:
            content = file.readlines()
        return content

    @staticmethod
    def _write_data(path: str, data: List[str]) -> None:
        """
        Handles writing data to a specific file
        :param path: Path of a file to write to
        :param data: Desired content of file
        """
        # Check if write will involve a non-existent subdirectory
        subdir = os.path.dirname(path)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        with open(path, "wt", encoding="utf-8") as file:
            file.writelines(data)

    @staticmethod
    def _run_command(command: List[str]) -> Tuple[str, str]:
        """
        Handles running commands in subprocess
        :param command: List of seperated command to run
        :return: stdout and stderr from command
        """
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            proc.wait()
            out = proc.stdout.read().decode("utf-8")
            err = proc.stderr.read().decode("utf-8")
        return out, err

    def build_test_harness(self, assumptions) -> None:
        """
         Constructs and compiles the tests harness consisting of
         the unit tests and the tests verifier
        :param assumptions: Assumptions extracted from the witness
        """
        self._build_unit_test()
        self._build_test_verifier(assumptions)
        _, _ = self._compile_test_harness()

    def _build_unit_test(self) -> None:
        """
        Constructs the unit tests from Test.java
        """
        test_data = self._read_data(self.TEST_RESOURCE_PATH)
        self._write_data(self.test_path, test_data)

    def _build_test_verifier(self, assumptions) -> None:
        """
        Constructs the tests verifier from a list of assumptions
        and Verifier.java
        :param assumptions: Assumptions extracted from the witness
        """
        verifier_path = os.path.join(
            self.directory, f"{self.VERIFIER_PACKAGE}/Verifier.java"
        )
        # Map assumptions to string form, mapping None to null
        string_assumptions = [
            f'"{a}"' if a is not None else "null" for a in assumptions
        ]
        verifier_data = self._read_data(self.VERIFIER_RESOURCE_PATH)
        # Replace empty assumptions list with extracted assumptions
        assumption_line = verifier_data.index(
            "  static String[] assumptionList = {};\n"
        )
        verifier_data[assumption_line] = verifier_data[assumption_line].replace(
            "{}", "{" + ", ".join(string_assumptions) + "}"
        )
        self._write_data(verifier_path, verifier_data)

    def _compile_test_harness(self) -> Tuple[str, str]:
        """
        Compiles the tests harness
        :return: stdout and stderr from compilation
        """
        compile_args = ["javac", "-sourcepath", self.directory, self.test_path]
        out, err = self._run_command(compile_args)
        return out, err

    def run_test_harness(self) -> str:
        """
        Runs the tests harness and reports the outcome of the validation execution
        :return: The validation result
        """
        run_args = ["java", "-cp", self.directory, "-ea", "Test"]
        out, err = self._run_command(run_args)
        # Set output to be stderr if there is some erroneous output
        out = err if err else out
        if 'Exception in thread "main" java.lang.AssertionError' in out:
            return "wit4java: Witness Correct"
        if "wit4java: Witness Spurious" in out:
            return "wit4java: Witness Spurious"
        return "wit4java: Could not validate witness"
