import sys
import os

import re
import networkx as nx


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
        regex = r"= (\d+)|\w+\.equals\(\"(\w*)\"\)"
    else: # assume producer is JBMC if not specified
        regex = r"= (\d+|null)\W"

    assumptions = {}
    for assump_edge in filter(lambda edge: ("assumption.scope" in edge[2]), witness_file.edges(data=True)):
        data = assump_edge[2]
        program = data["originFileName"]
        program = program[program.rfind("/") + 1: program.find(".java")]
        scope = data["assumption.scope"]
        if program not in scope:
            continue;

        assumption = data["assumption"]
        search_result = re.search(regex, assumption)
        if search_result is None:
            continue

        assumption_value = search_result.group(1) or search_result.group(2)
        if producer != "GDart" and assumption_value == "null":
            assumption_value = None

        start_line = data["startline"]

        if program not in assumptions:
            assumptions[program] = {}
        assumptions[program][start_line] = assumption_value

    return assumptions
