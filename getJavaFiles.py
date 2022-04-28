#!/usr/bin/env python3
import sys
import glob

def _find_between(s, start, end):
    return (s.split(start))[1].split(end)[0]

def _getLinesToType(filename):
    with open(filename, "r") as f:
        lines_to_type = {}
        for line_number, line in enumerate(f, 1):
            search_string = "Verifier.nondet"
            if search_string in line:
                type = _find_between(line, "nondet", "(")
                lines_to_type[line_number] = type
        return lines_to_type

# NOTE: pass nothing or "<./>" to search in current directory
def getFilesToLinesToType(path):
    files_to_lines_to_type = {}

    source_files = [f for f in glob.glob(path + "**/*.java", recursive=True)]
    for filename in source_files:
        lines_to_type = _getLinesToType(filename)
        files_to_lines_to_type[filename] = lines_to_type
        
    print(files_to_lines_to_type)
    return files_to_lines_to_type

source_dir = "" 
getFilesToLinesToType(source_dir)


