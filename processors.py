import glob
import re
import networkx as nx
import os
from distutils.dir_util import copy_tree


def _find_between(s, start, end):
    return (s.split(start))[1].split(end)[0]


def _get_lines_to_type(filename):
    with open(filename, "r") as f:
        lines_to_type = {}
        for line_number, line in enumerate(f, 1):
            search_string = "Verifier.nondet"
            if search_string in line:
                type = _find_between(line, "nondet", "(")
                lines_to_type[line_number] = type.lower()
        return lines_to_type

def process_java_files(path):
    source_files = [f for f in glob.glob(path + "**/*.java", recursive=True)]
    for file in source_files:
        with open(file, "rt") as fi:
            for line in fi:
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

    return copy_tree(path, './')

# NOTE: pass nothing or "<./>" to search in current directory
def extract_types(path):
    types_map = {}
    source_files = [f for f in glob.glob(path + "**/*.java", recursive=True)]
    for filename in source_files:
        program_name = filename[filename.rfind("/") + 1: filename.find(".java")]
        with open(filename, "r") as f:
            for line_number, line in enumerate(f, 1):
                search_string = "Verifier.nondet"
                if search_string in line:
                    type = _find_between(line, "nondet", "(")
                    types_map[(program_name, line_number)] = type.lower()
    return types_map


def extract_assumptions(witness_file_dir):
    witness_file = None
    try:
        witness_file = nx.read_graphml(witness_file_dir)
    except Exception as e:
        print("Exception: could not read witness file")
        print(e)
        exit(0)

    producer = None
    if "producer" in witness_file.graph:
        producer = witness_file.graph["producer"]

    regex = None
    if producer == "GDart":
        regex = r"= (-?\d*\.?\d+|false|true)|\w+\.equals\(\"(.*)\"\)|\w+\.parseDouble\(\"(.*)\"\)|\w+\.parseFloat\(\"(.*)\"\)"
    else:  # assume producer is JBMC if not specified
        regex = r"= (-?\d*\.?\d+|false|true|null)\W"

    assumptions = []
    for assump_edge in filter(lambda edge: ("assumption.scope" in edge[2]), witness_file.edges(data=True)):
        data = assump_edge[2]
        program = data["originFileName"]
        file_name = program[program.rfind("/") + 1: program.find(".java")]
        scope = data["assumption.scope"]
        if file_name not in scope:
            continue

        assumption = data["assumption"]
        search_result = re.search(regex, assumption)
        if search_result is not None:
            assumption_value = search_result.group(1) or search_result.group(2) or search_result.group(3) or search_result.group(4)
        else:
            # Check to see if it is because nondet comes from a function return
            # this occurs when the assumption.scope field ends in Z and in which
            # case the assumption value is the whole assumption field
            regex = regex[2:]
            search_result = re.search(regex, assumption)
            if search_result is not None:
                assumption_value = search_result.group(1) or search_result.group(2)
            else:
                continue


        # TODO: Might not be necessary
        if producer != "GDart" and assumption_value == "null":
           assumption_value = None

        start_line = data["startline"]
        assumptions.append(((file_name, start_line), assumption_value))

    return assumptions

def construct_type_assumption_pairs(file_line_type_map, assumptions_list):
    # Get all assumption positions
    assumptions_position_list = [assumption_position for (assumption_position, _ ) in assumptions_list]
    # Check each nondet call has greater than one assumption
    if not all(position in assumptions_position_list for position in file_line_type_map.keys()):
        raise ValueError('Not all nondet calls have been assigned assumptions, cannot verify.')
    # Map each assumption to its respective
    type_assumption_pairs = [(file_line_type_map[position], value) for (position, value) in assumptions_list
                             if position in file_line_type_map]
    return type_assumption_pairs