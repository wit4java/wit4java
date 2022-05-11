#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the path of networkx to run benchexec. Should 'pip install networkx' first
sys.path.append("/home/joss/.local/lib/python3.8/site-packages")


from output import UnitTestBuilder
from processors import extract_assumptions, extract_types, process_java_files

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
        print(os.getcwd())
        java_common_path = sys.argv[3]
        java_files_path = sys.argv[4]
        # Need to preprocess and move to current directory to utilise mockito
        teardown_files = process_java_files(java_files_path)
        # Process files to get maps
        file_line_type_map = extract_types(java_files_path)
        file_line_assumption_map = extract_assumptions(witness_file_dir)

        # Check that for each nondet call we have an assumption and populate our list of type, assumptions pairs
        type_assumption_pairs = []
        for file_name, line_type_map in file_line_type_map.items():
            for line, type in line_type_map.items():
                # Check non mapping
                if file_name in file_line_assumption_map and line in file_line_assumption_map[file_name]:
                    assumptions = file_line_assumption_map[file_name][line]
                    pairs = [(type, assumption) for assumption in assumptions]
                    type_assumption_pairs.extend(pairs)
        # Check for each type from java file we have an assumptions
        utb = UnitTestBuilder(type_assumption_pairs)
        utb.build_unit_test('Test.java')

        cmd = "javac -cp {} Test.java".format(os.getenv('CLASSPATH'))
        subprocess.Popen(cmd, shell=True).wait()

        cmd1 = "java -ea Test"
        subprocess.Popen(cmd1, shell=True).wait()

        # Delete copied files
        for file in teardown_files:
            os.remove(file)


except BaseException as e:
   print('Exception: ' + str(e))
exit(0)

