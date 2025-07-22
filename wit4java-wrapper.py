#!/usr/bin/env python3

import os, sys
import argparse
import subprocess
import shlex

parser = argparse.ArgumentParser()

parser.add_argument("files", nargs="*", help="Path to the packages")
# parser.add_argument("benchmark", nargs='?', help="Path to the benchmark")
parser.add_argument("--witness", help="witness file")
parser.add_argument("-v", "--version", help="wit4java version", action="store_true")
parser.add_argument(
    "--local-dir",
    help="perform all of the processing in the current directory",
    action="store_true",
)
args = parser.parse_args()

# benchmark = args.benchmark
files = args.files
witness = args.witness
version = args.version
local_dir = args.local_dir

path = str(os.path.split(os.path.abspath(sys.argv[0]))[0])
path = str(os.path.split(sys.argv[0])[0])
# print(path)
command_line = path + "/bin/wit4java"

if version:
    print("3.0")
    # print(os.popen(esbmc_path + "--version").read()[6:].strip()),
    exit(0)

if files is None:
    print("please specify source program")
    exit(1)

if local_dir:
    command_line += " " + "--local-dir"
benchmark = files[-1]
packages = files[0:-1]

command_line += " " + benchmark

if packages is not None:
    command_line += " " + "--packages"
    for package in packages:
        command_line += " " + package

if witness is None:
    print("please specify witness")
    exit(1)

command_line += " " + "--witness " + witness

print(command_line)


the_args = shlex.split(command_line)
p = subprocess.Popen(the_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(stdout, stderr) = p.communicate()
print(stdout.decode())
print(stderr.decode())
