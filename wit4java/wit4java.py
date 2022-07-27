#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile

from shutil import rmtree

import argparse

from wit4java.testharness import TestHarness
from wit4java.processors import JavaFileProcessor, WitnessProcessor, construct_type_assumption_pairs
from wit4java import __version__


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")


def create_argument_parser():
    parser = argparse.ArgumentParser(
        description="""
                   Validate a given Java program with a witness conforming to the appropriate SV-COMP
                   exchange format.
               """,
    )

    parser.add_argument(
        'benchmark',
        type=dir_path,
        help="Path to the benchmark directory"
    )

    parser.add_argument(
        '--packages',
        dest='package_paths',
        type=dir_path,
        nargs='*',
        help="Path to the packages used by the benchmark"
    )

    parser.add_argument(
        '--witness',
        dest='witness_file',
        required=True,
        type=str,
        action="store",
        help='Path to the witness file. Must conform to the exchange format'
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    return parser


def main():
    parser = create_argument_parser()
    config = parser.parse_args(sys.argv[1:])
    config = vars(config)
    try:
        print(f'wit4java version: {__version__}')
        print("witness: ", config['witness_file'])

        # Create temporary directory for easier cleanup
        tmp_dir = tempfile.mkdtemp()

        # Instantiate file processors
        jfp = JavaFileProcessor(tmp_dir, config['benchmark'], config['package_paths'])
        wfp = WitnessProcessor(tmp_dir, config['witness_file'])

        # Need to preprocess and move to current directory to utilise mockito
        jfp.preprocess()
        wfp.preprocess()

        # Process files to get type mapping and assumption list
        assumptions = wfp.assumptions

        # Construct tests harness
        test_harness = TestHarness(tmp_dir)
        test_harness.build_test_harness(assumptions)
        outcome = test_harness.run_test_harness()
        print(outcome)

        # Teardown moved files
        rmtree(tmp_dir)

    except RuntimeError as e:
        print(f'wit4java: Could not validate witness \n{e}')
    sys.exit()


if __name__ == "__main__":
    main()
