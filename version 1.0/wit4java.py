#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
from subprocess import Popen, PIPE, CalledProcessError
import xml.etree.ElementTree as ET
from fnmatch import fnmatch
from sys import exit

# Add the path of networkx to run benchexec. Should 'pip install networkx' first
# sys.path.append('/home/tong/.local/lib/python3.8/site-packages')

import networkx as nx


def takeFirst(elem):
    return elem[0]


def last_str(str):
    if str.rfind(" ") == -1:
        return str.strip()
    else:
        return str[str.rindex(" ") + 1 :].strip()


try:
    # missing witness or java files
    if len(sys.argv) <= 3:
        if sys.argv[1] == "--version":
            print("1.0")
        exit(0)
    else:
        print("wit4java version: 1.0")
        witness_File_Dir = sys.argv[2]
        print("witness: ", witness_File_Dir)
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

        if Witness:
            witness_type = witnessFile.graph["witness-type"]
            if witness_type == "violation_witness":
                for benchmark in benchmarks_dir:
                    new_benchmark_dir = ""
                    counterexample = []

                    for data in witnessFile.edges(data=True):
                        if (
                            data[2]["originFileName"] in benchmark
                            and "assumption.scope" in data[2]
                        ):
                            scope = data[2]["assumption.scope"]
                            startLine = data[2]["startline"]
                            if (
                                benchmark[
                                    benchmark.rfind("/") + 1 : benchmark.find(".java")
                                ]
                                in scope
                                or "java" == scope
                            ):
                                assumption = data[2]["assumption"]
                                ##print(assumption)
                                counterexample.append(tuple((startLine, assumption)))

                    counterexample.sort(key=takeFirst)
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
                    with open(benchmark, "r") as fii:
                        with open(
                            os.path.join(new_benchmark_dir, filename), "wt"
                        ) as newfi:
                            for position, line1 in enumerate(fii, 1):
                                line_new = line1
                                if len(counterexample) != 0:
                                    while position == counterexample[0][0]:
                                        str = counterexample[0][1]
                                        if str[len(str) - 1] != ";":
                                            str = str + ";"

                                        if (
                                            "++" in line1
                                            or "--" in line1
                                            or "*=" in line1
                                        ):
                                            line_new = line1

                                        else:
                                            try:
                                                if (
                                                    last_str(
                                                        line1[
                                                            : line1.index("=")
                                                        ].strip()
                                                    )
                                                    == str[: str.index("=")].strip()
                                                ):
                                                    if "&" not in str:
                                                        line_new = line_new.replace(
                                                            line_new[
                                                                line_new.index(
                                                                    "="
                                                                ) : line_new.rindex(";")
                                                            ].strip(),
                                                            str[
                                                                str.index(
                                                                    "="
                                                                ) : str.rindex(";")
                                                            ].strip(),
                                                        )
                                            except:
                                                line_new = line1
                                        counterexample.remove(counterexample[0])

                                        if len(counterexample) == 0:
                                            break

                                if (
                                    " void " in line1
                                    and " main" in line1
                                    and "public " not in line1
                                ):
                                    line_new = "public " + line_new
                                newfi.write(line_new)
                        with open(new_benchmark_dir, filename, "r") as newfii:
                            for line2 in newfii:
                                if "return" not in line2 and "Verifier.nondet" in line2:
                                    print("unknown")
                                    exit(0)

                cmd = "javac Main.java"
                subprocess.Popen(cmd, shell=True).wait()

                cmd1 = "java -ea Main"
                # p = subprocess.Popen(cmd1,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
                validate = "F"
                with Popen(
                    cmd1,
                    shell=True,
                    stdout=PIPE,
                    stderr=PIPE,
                    bufsize=1,
                    universal_newlines=True,
                ) as p:
                    for line in p.stderr:
                        if "AssertionError" in line:
                            validate = "T"
                        print(line, end="")

                # output = p.communicate()[0]
                # print(output)
                if validate == "F":
                    print("Ok ")

except Exception as e:
    print(e)

exit(0)
