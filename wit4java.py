#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the path of networkx to run benchexec. Should 'pip install networkx' first
sys.path.append("/home/joss/.local/lib/python3.8/site-packages")


from output import UnitTestBuilder
from processors import process_java_files, extract_assumptions, extract_types, construct_type_assumption_pairs

# How to call this script:
# ./wit4java.py --witness witness.graphml source1 source2
# or
# ./wit4java.py --version

try:
    if len(sys.argv) <= 3:
        if sys.argv[1] == "--version":
            print("2.0")
        # missing witness or java files
        exit(0)
    else:
        print("wit4java version: 2.0")
        witness_file_dir = sys.argv[2]
        print("witness: ", witness_file_dir)
        # Have to do this for benchexec
        # TODO: better name
        java_commons_paths = sys.argv[3:-1]
        java_files_path = sys.argv[-1]

        # Need to preprocess and move to current directory to utilise mockito
        teardown_files = process_java_files(java_files_path)

        # Process files to get maps
        file_line_type_map = extract_types(java_files_path)
        assumptions_list = extract_assumptions(witness_file_dir)

        # Construct ordered (type , assumption) pairs
        type_assumption_pairs = construct_type_assumption_pairs(file_line_type_map, assumptions_list)

        # Check for each type from java file we have an assumptions
        utb = UnitTestBuilder(type_assumption_pairs)
        utb.build_unit_test('Test.java')

        cmd = "javac -cp {0}:{1} Test.java".format(os.getenv('CLASSPATH'), ':'.join(java_commons_paths))
        subprocess.Popen(cmd, shell=True).wait()

        cmd1 = "java -ea Test"
        subprocess.Popen(cmd1, shell=True).wait()

        # Delete copied files
        for file in teardown_files:
           os.remove(file)


except BaseException as e:
   print('Exception: ' + str(e))
exit(0)
