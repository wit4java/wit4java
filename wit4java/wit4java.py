#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile

from shutil import rmtree

import argparse

from wit4java.output.builders import TestHarnessBuilder, build_unit_test
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
                   Validate a given Java program with a witness conforming to the appropriate exchange format SV-COMP
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
        help='Path to the witness file. Must conform to the following format '
             'https://github.com/sosy-lab/sv-witnesses/blob/main/README-GraphML.md.'
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    return parser


def main():
    try:
        parser = create_argument_parser()
        config = parser.parse_args(sys.argv[1:])
        config = vars(config)
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
        file_line_type_map = jfp.extract()
        assumptions_list = wfp.extract

        # Construct ordered (type , assumption) pairs
        type_assumption_pairs = construct_type_assumption_pairs(
            file_line_type_map,
            assumptions_list
        )

        # Check for each type from java file we have an assumptions
        test_path = os.path.join(tmp_dir, 'Test.java')
        build_unit_test(test_path)

        vhb = TestHarnessBuilder(type_assumption_pairs)
        harness_path = os.path.join(tmp_dir, 'org/sosy_lab/sv_benchmarks/Verifier.java')
        vhb.build_test_harness(harness_path)

        # Compile Test class
        compile_args = ['javac', '-sourcepath', tmp_dir, test_path]
        with subprocess.Popen(compile_args,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            p.wait()

        # Run test
        run_args = ['java', '-cp', tmp_dir, '-ea', 'Test']
        with subprocess.Popen(run_args,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            out = p.stdout.read().decode("utf-8")
            err = p.stderr.read().decode("utf-8")

            # Set output to be stderr if there is some erroneous output
            out = err if err else out
            if 'Exception in thread "main" java.lang.AssertionError' in out:
                print('wit4java: Witness Correct')
            elif 'wit4java: Witness Spurious' in out:
                print('wit4java: Witness Spurious')
            else:
                print('wit4java: Could not validate witness')

        # Teardown moved files
        rmtree(tmp_dir)

    except BaseException as e:
        print(f'wit4java: Could not validate witness \n{e}')
    sys.exit()


if __name__ == "__main__":
    main()
