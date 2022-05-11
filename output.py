class UnitTestBuilder():

    FILE_HEADER = 'import org.mockito.*;'\
                  '\nimport org.mockito.stubbing.OngoingStubbing;'\
                  '\nimport org.sosy_lab.sv_benchmarks.Verifier;'\
                  '\n\npublic class Test {'\
                  '\n\tpublic static void main(String[] args) {'\
                  '\n\t\tMockito.mockStatic(Verifier.class);'

    VIOLATION_BLOCK = '\ntry {'\
                      '\n\tMain.main(new String[0]);'\
                      '\n\tSystem.out.println("OK ");'\
                      '\n} catch (Exception e) {'\
                      '\n\tSystem.out.println(e);'\
                      '\n}'

    MOCKITO_STUB_INITS = {
        'int': 'OngoingStubbing <Integer> stubbing_int = Mockito.when(Verifier.nondetInt());',
        'short': 'OngoingStubbing <Short> stubbing_short = Mockito.when(Verifier.nondetShort());',
        'long': 'OngoingStubbing <Long> stubbing_long = Mockito.when(Verifier.nondetLong());',
        'float': 'OngoingStubbing <Float> stubbing_float = Mockito.when(Verifier.nondetFloat());',
        'double': 'OngoingStubbing <Double> stubbing_double = Mockito.when(Verifier.nondetDouble());',
        'boolean': 'OngoingStubbing <Boolean> stubbing_boolean = Mockito.when(Verifier.nondetBoolean());',
        'char': 'OngoingStubbing <Character> stubbing_char = Mockito.when(Verifier.nondetChar());',
        'byte': 'OngoingStubbing <Byte> stubbing_byte = Mockito.when(Verifier.nondetByte());}',
        'string': 'OngoingStubbing <String> stubbing_string = Mockito.when(Verifier.nondetString());'
    }

    MOCKITO_THEN_RETURNS = {
        'int': 'stubbing_int = stubbing_int.thenReturn(Integer.parseInt(assumptions[i]));',
        'short': 'stubbing_short = stubbing_short.thenReturn(Short.parseShort(assumptions[i]));',
        'long': 'stubbing_long = stubbing_long.thenReturn(Long.parseLong(assumptions[i]));',
        'float': 'stubbing_float = stubbing_float.thenReturn(Float.parseFloat(assumptions[i]));',
        'double': 'stubbing_double = stubbing_double.thenReturn(Double.parseDouble(assumptions[i]));',
        'boolean': 'stubbing_boolean = stubbing_boolean.thenReturn(Boolean.parseBoolean(assumptions[i]));',
        'char': 'stubbing_char = stubbing_char.thenReturn((char)Integer.parseInt(assumptions[i]));',
        'byte': 'stubbing_byte = stubbing_byte.thenReturn((byte)Integer.parseInt(assumptions[i]));',
        'string': 'stubbing_string = stubbing_string.thenReturn(assumptions[i]);'
    }

    def __init__(self, type_assumption_list):
        self.types = [tv[0].strip() for tv in type_assumption_list]
        self.assumptions = [tv[1].strip() for tv in type_assumption_list]

    def _gen_assumptions_line(self):
        # Map assumptions to string form, mapping None to null
        string_assumptions = ['"{}"'.format(a) if a is not None else 'null' for a in self.assumptions]
        return '\nString[] assumptions = {' + ', '.join(string_assumptions) + '};'

    def _gen_types_line(self):
        return '\nString[] types = {"' + '", "'.join(self.types) + '"};'

    def _gen_stubbing_init_block(self):
        unique_types = set(self.types)
        required_stubs = [self.MOCKITO_STUB_INITS[type] for type in unique_types]
        return "\n" + "\n".join(required_stubs)

    def _gen_stubbing_switch_block(self):
        from textwrap import indent
        unique_types = set(self.types)
        required_switch_blocks = [self._gen_stubbing_case_block(type) for type in unique_types]
        return '\nswitch(types[i]) {' + indent("\n".join(required_switch_blocks), '\t') + '\n}'

    def _gen_stubbing_case_block(self, type):
        return '\ncase "{0}":\n\t{1}\n\tbreak;'.format(type, self.MOCKITO_THEN_RETURNS[type])

    def _gen_unit_test(self):
        from textwrap import indent
        content = self.FILE_HEADER
        # Add assumption and types
        content += indent(self._gen_types_line(), '\t\t')
        content += indent(self._gen_assumptions_line(), '\t\t')
        # Initialise the mocking variables
        content += indent(self._gen_stubbing_init_block(), '\t\t')
        # Add for loop to add mocking returns for each of the assumptions
        content += indent('\nfor (int i = 0; i < types.length; i++) {', '\t\t')
        # Add switch block to loop
        content += indent(self._gen_stubbing_switch_block(), '\t\t\t')
        content += indent('\n}', '\t\t')
        # Add violation block
        content += indent(self.VIOLATION_BLOCK, '\t\t')
        content += indent('\n}', '\t')
        content += '\n}'
        return content

    def build_unit_test(self, path):
        with open(path, "wt") as f:
            f.writelines(self._gen_unit_test())