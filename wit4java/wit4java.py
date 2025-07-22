"""
 This file is part of wit4java, an execution-based violation-witness validator for Java
 https://github.com/wit4java/wit4java.

 This module deals with the main functionality of the tool
"""

import os
import sys
import tempfile

from shutil import rmtree

import argparse

from wit4java.testharness import TestHarness
from wit4java.processors import JavaFileProcessor, WitnessProcessor, filter_assumptions
from wit4java import __version__


def dir_path(path):
    """
    Checks if a path is a valid directory
    :param path: Potential directory
    :return: The original path if valid
    """
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Creates a parser for the command-line options.
    @return: An argparse.ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="""
                   Validate a given Java program with a witness conforming to the appropriate SV-COMP
                   exchange format.
               """,
    )

    parser.add_argument(
        "benchmark", type=dir_path, help="Path to the benchmark directory"
    )

    parser.add_argument(
        "--packages",
        dest="package_paths",
        type=dir_path,
        nargs="*",
        help="Path to the packages used by the benchmark",
    )

    parser.add_argument(
        "--witness",
        dest="witness_file",
        required=True,
        type=str,
        action="store",
        help="Path to the witness file. Must conform to the exchange format",
    )

    parser.add_argument(
        "--local-dir",
        help="perform all of the processing in the current directory",
        action="store_true",
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    parser.add_argument(
        "--json-input",
        dest="json_input",
        action="store_true",
        default=False,
        help="Interpret the witness input with JSON/YAML format",
    )

    return parser


def main():
    parser = create_argument_parser()
    config = parser.parse_args(sys.argv[1:])
    config = vars(config)
    try:
        print(f"wit4java version: {__version__}")
        print("witness: ", config["witness_file"])

        # Create temporary directory for easier cleanup
        directory = "." if config["local_dir"] else tempfile.mkdtemp()

        # Instantiate file processors
        jfp = JavaFileProcessor(directory, config["benchmark"], config["package_paths"])
        wfp = WitnessProcessor(directory, config["witness_file"])

        # Need to preprocess and move to current directory to utilise mockito
        jfp.preprocess()
        wfp.preprocess()

        # Process files to get type mapping and assumption list
        assumptions = wfp.extract_assumptions()
        nondet_mappings = jfp.extract_nondet_mappings()
        assumption_values = filter_assumptions(nondet_mappings, assumptions)
        # Construct tests harness
        test_harness = TestHarness(directory)
        test_harness.build_test_harness(assumption_values)
        outcome = test_harness.run_test_harness()
        print(outcome)

        # Teardown moved files if not in local directory
        if not config["local_dir"]:
            rmtree(directory)

    except BaseException as err:
        print(f"wit4java: Could not validate witness \n{err}")
    sys.exit()


if __name__ == "__main__":
    main()
