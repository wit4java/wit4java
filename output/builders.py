import os


def _gen_unit_test():
    resource_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resources/Test.java'
    )
    with open(resource_path, 'r') as file:
        content = file.readlines()
    return content


def build_unit_test(path):
    with open(path, "wt") as f:
        f.writelines(_gen_unit_test())


class VerifierBuilder():

    def __init__(self, type_assumption_list):
        self.assumptions = [tv[1].strip() for tv in type_assumption_list]

    def build_test_harness(self, path):
        # Map assumptions to string form, mapping None to null
        string_assumptions = [f'"{a}"' if a is not None else 'null' for a in self.assumptions]
        # Check if incoming path involves a new subdirectory
        subdir = os.path.dirname(path)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        resource_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'resources/Verifier.java'
        )
        with open(resource_path, 'r') as file:
            # read a list of lines into data
            data = file.readlines()
        assumption_line = data.index('  #assumptionList\n')
        data[assumption_line] = '  static String[] assumptionList = {' + ', '.join(string_assumptions) + '};\n'

        with open(path, 'w') as file:
            file.writelines(data)
