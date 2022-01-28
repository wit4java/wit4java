#!/usr/bin/env python3
import sys
import os
import subprocess
from fnmatch import fnmatch

# Add the path of networkx to run benchexec. Should 'pip install networkx' first
# sys.path.append("/home/tong/.local/lib/python3.8/site-packages")

import networkx as nx

# How to call this script:
# ./wit4java.py --witness witness.graphml source1 source2
# or
# ./wit4java.py --version

try:
    if len(sys.argv) <= 3:
        if sys.argv[1] == "--version":
            print("1.0")
        # missing witness or java files
        exit(0)
    else:
        print("wit4java version: 1.0")
        witness_File_Dir = sys.argv[2]
        print("witness: ", witness_File_Dir)

        # find all java source files from inputs
        benchmarks_dir = []
        for i in sys.argv[3:]:
            if ".java" in i:
                benchmarks_dir.append(i)

            else:
                for path, subdirs, files in os.walk(i):
                    for name in files:
                        if fnmatch(name, "*.java"):
                            benchmarks_dir.append(os.path.join(path, name))
        print("benchmark: ", benchmarks_dir)

        try:
            witnessFile = nx.read_graphml(witness_File_Dir)
            Witness = False
            for violationKey in witnessFile.nodes(data=True):
                if "isViolationNode" in violationKey[1]:
                    Witness = True
        except Exception as e:
            print("Exception: unknown witness.")
            print(e)
            Witness = False
            exit(0)

        # violation-witness validation
        if Witness:
            dict_line_type = {}
            assump = []
            witness_type = witnessFile.graph["witness-type"]
            producer = witnessFile.graph["producer"]
            if witness_type == "violation_witness":
                # Store all file names in a string
                files = ""
                for file in benchmarks_dir:
                    files = file + ";" + files

                for benchmark in benchmarks_dir:
                    new_benchmark_dir = ""
                    content = []
                    dict = {}
                    dict1 = {}
                    with open(benchmark, "rt") as fi:
                        for line in fi:
                            filename = benchmark[benchmark.rindex("/") + 1 :]
                            if line.strip().find("package") == 0:
                                new_benchmark_dir = (
                                    line.strip()
                                    .replace(".", "/")
                                    .replace(";", "")
                                    .replace("package", "")
                                    .replace(" ", "")
                                )
                                if not os.path.exists(new_benchmark_dir):
                                    os.makedirs(new_benchmark_dir)
                                break
                    # record verifier call positions and statements
                    with open(benchmark, "r") as fii:
                        with open(
                            os.path.join(new_benchmark_dir, filename), "wt"
                        ) as newfi:
                            for position, line1 in enumerate(fii, 1):
                                content.append(line1)
                                if "Verifier.nondet" in line1:
                                    dict[position] = line1

                                line_new = line1
                                if (
                                    " void " in line1
                                    and " main" in line1
                                    and "public " not in line1
                                ):
                                    line_new = "public " + line_new
                                newfi.write(line_new)
                            for key, values in dict.items():
                                type = values[
                                    values.index("nondet") + 6 : values.rindex("(")
                                ].lower()
                                if " return " in values and producer != "GDart":
                                    # type = values[values.index('nondet')+6:values.rindex('(')].lower()
                                    fuc = content[key - 2][
                                        content[key - 2].index("boolean")
                                        + 8 : content[key - 2].rindex("(")
                                    ]

                                    for num, i in enumerate(content, 1):
                                        if fuc in i and i is not content[key - 2]:
                                            dict1[num] = type

                                else:
                                    dict1[key] = type
                    # dict_line_type:Dictionary (file name, (line number, type))
                    dict_line_type[benchmark[benchmark.rfind("/") + 1 :]] = dict1

                for data in witnessFile.edges(data=True):
                    program = data[2]["originFileName"]
                    program = program[program.rfind("/") + 1 :]
                    if program in files and "assumption.scope" in data[2]:
                        # program is a string containing only 'file.java'
                        scope = data[2]["assumption.scope"]
                        startLine = data[2]["startline"]

                        if program[: program.find(".java")] in scope and dict_line_type[
                            program
                        ].__contains__(startLine):
                            ##print(assumption)
                            assumption = data[2]["assumption"]
                            if assumption[len(assumption) - 1] != ";":
                                assumption = assumption + ";"

                            if assumption.find("=") == -1:
                                assumption = " = " + assumption
                            assumptionValue = assumption[
                                assumption.index("=") + 1 : assumption.index(";")
                            ]

                            assignd = False
                            for assu in assump:
                                if program + str(startLine) in assu[1]:
                                    assu[1] = assumptionValue
                                    assignd = True
                                    break
                            if not assignd:
                                assump.append(
                                    list(
                                        (
                                            dict_line_type[program][startLine],
                                            assumptionValue,
                                        )
                                    )
                                )
                    elif program in files:
                        startLine = data[2]["startline"]

                        if dict_line_type[program].__contains__(startLine):

                            assump.append(
                                list(
                                    (
                                        dict_line_type[program][startLine],
                                        program + str(startLine) + " novalue",
                                    )
                                )
                            )
                Type = ""
                Assumption = ""
                for ass in assump:
                    Type = Type + ";" + ass[0].strip()
                    if "novalue" in ass[1]:
                        print("unknown")
                        exit(0)
                    Assumption = Assumption + ";" + ass[1].strip()

                int_type = False
                short_type = False
                long_type = False
                float_type = False
                double_type = False
                boolean_type = False
                char_type = False
                byte_type = False

                if "string" in Type:
                    exit(0)
                if "int" in Type:
                    int_type = True
                if "short" in Type:
                    short_type = True
                if "long" in Type:
                    long_type = True
                if "float" in Type:
                    float_type = True
                if "double" in Type:
                    double_type = True
                if "boolean" in Type:
                    boolean_type = True
                if "char" in Type:
                    char_type = True
                if "byte" in Type:
                    byte_type = True

                with open("test.txt", "rt") as fin:
                    with open("test.java", "wt") as fout:
                        for line in fin:
                            line = line.replace("Type", Type)
                            line = line.replace("Assumption", Assumption)
                            if int_type and "stubbing_int" in line:
                                line = line.replace("//", "")
                            if short_type and "stubbing_short" in line:
                                line = line.replace("//", "")
                            if long_type and "stubbing_long" in line:
                                line = line.replace("//", "")
                            if float_type and "stubbing_float" in line:
                                line = line.replace("//", "")
                            if double_type and "stubbing_double" in line:
                                line = line.replace("//", "")
                            if boolean_type and "stubbing_boolean" in line:
                                line = line.replace("//", "")
                            if char_type and "stubbing_char" in line:
                                line = line.replace("//", "")
                            if byte_type and "stubbing_byte" in line:
                                line = line.replace("//", "")

                            line = line.replace("ClassName", "Main")
                            fout.write(line)

                cmd = "javac test.java"
                subprocess.Popen(cmd, shell=True).wait()

                cmd1 = "java -ea test"
                subprocess.Popen(cmd1, shell=True).wait()

except Exception as e:
    print(e)

exit(0)
