#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile

from shutil import rmtree
from output.builders import UnitTestBuilder
from output.builders import VerifierBuilder
from processors import JavaFileProcessor, WitnessProcessor, construct_type_assumption_pairs

sys.path.append("/home/joss/.local/lib/python3.8/site-packages")

# How to call this script:
# ./wit4java.py --witness witness.graphml source1 source2
# or
# ./wit4java.py --version

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
        dirpath = tempfile.mkdtemp()

        # Instantiate file processors
        jfp = JavaFileProcessor(dirpath, benchmark_path, package_paths)
        wfp = WitnessProcessor(dirpath, witness_path)

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
        utb = UnitTestBuilder(type_assumption_pairs)
        test_path = os.path.join(dirpath, 'Test.java')
        utb.build_unit_test(test_path)

        vhb = VerifierBuilder(type_assumption_pairs)
        harness_path = os.path.join(dirpath, 'org/sosy_lab/sv_benchmarks/Verifier.java')
        vhb.build_test_harness(harness_path)

        cmd = f"javac {test_path}"
        subprocess.Popen(cmd, cwd=dirpath, shell=True).wait()

        cmd1 = "java -ea Test"
        subprocess.Popen(cmd1, cwd=dirpath, shell=True).wait()

        # Teardown moved files
        rmtree(dirpath)


except BaseException as e:
    print('Exception: ' + str(e))
sys.exit()
