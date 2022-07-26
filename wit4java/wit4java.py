#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile

from shutil import rmtree
from wit4java.output.builders import VerifierBuilder, build_unit_test
from wit4java.processors import JavaFileProcessor, WitnessProcessor, construct_type_assumption_pairs


# How to call this script:
# ./wit4java.py --witness witness.graphml source1 source2
# or
# ./wit4java.py --version

def main():
    try:
        if len(sys.argv) <= 3:
            if sys.argv[1] == "--version":
                print("2.0")
            # missing witness or java files
            sys.exit(0)
        else:
            print("wit4java version: 2.0")
            witness_path = sys.argv[2]
            print("witness: ", witness_path)
            # Have to do this for benchexec
            package_paths = sys.argv[3:-1]
            benchmark_path = sys.argv[-1]

            # Create temporary directory for easier cleanup
            tmp_dir = tempfile.mkdtemp()

            # Instantiate file processors
            jfp = JavaFileProcessor(tmp_dir, benchmark_path, package_paths)
            wfp = WitnessProcessor(tmp_dir, witness_path)

            # Need to preprocess and move to current directory to utilise mockito
            jfp.preprocess()
            wfp.preprocess()

            # Process files to get type mapping and assumption list
            file_line_type_map = jfp.extract()
            assumptions_list = wfp.extract()

            # Construct ordered (type , assumption) pairs
            type_assumption_pairs = construct_type_assumption_pairs(
                file_line_type_map,
                assumptions_list
            )

            # Check for each type from java file we have an assumptions
            test_path = os.path.join(tmp_dir, 'Test.java')
            build_unit_test(test_path)

            vhb = VerifierBuilder(type_assumption_pairs)
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
                print()
                if err:
                    if 'Exception in thread "main" java.lang.AssertionError' not in err:
                        print(err)
                    else:
                        print(f'wit4java Exception: {err}')
                else:
                    print(out)
            # Teardown moved files
            rmtree(tmp_dir)


    except RuntimeError as e:
        print('wit4java Exception: ' + str(e))
    sys.exit()

if __name__ == "__main__":
    main()
