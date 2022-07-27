import os.path
import tempfile
import unittest
from shutil import rmtree
from os.path import exists

import sys
sys.path.append('../..')

from parameterized import parameterized
from wit4java.testharness import TestHarness


class TestTestHarness(unittest.TestCase):
    EMPTY_ASSUMPTIONS = []

    def assertFileEqual(self, expected_path, actual_path):
        with open(expected_path, 'r', encoding='utf-8') as expected_file:
            expected_file_lines = expected_file.readlines()
        with open(actual_path, 'r', encoding='utf-8') as actual_file:
            actual_file_lines = actual_file.readlines()
        return self.assertListEqual(
            expected_file_lines,
            actual_file_lines,
            'Files contents are not equal.'
        )

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_harness = TestHarness(self.tmp_dir)

    def tearDown(self):
        rmtree(self.tmp_dir)

    def test_unit_test_written_to_dir(self):
        self.test_harness.build_test_harness(self.EMPTY_ASSUMPTIONS)
        test_path = os.path.join(self.tmp_dir, 'Test.java')
        ref_path = '../../wit4java/resources/Test.java'
        self.assertTrue(exists(test_path), 'Test.java has not been created.')
        self.assertFileEqual(ref_path, test_path)

    @parameterized.expand([
        [[], 'resources/verifiers/VerifierWithNoAssumptions.java'],
        [['1', '-1', '10L'], 'resources/verifiers/VerifierWithIntegerAssumptions.java'],
        [['25f', '101.123456789123456789'], 'resources/verifiers/VerifierWithFloatingPointAssumptions.java'],
        [['true', 'false'], 'resources/verifiers/VerifierWithBooleanAssumptions.java'],
        [['a', 'b', 'c'], 'resources/verifiers/VerifierWithCharAssumptions.java'],
        [['non', 'determinism'], 'resources/verifiers/VerifierWithStringAssumptions.java']
    ])
    def test_assumptions_injected_to_verifier(self, assumptions, expected_output_path):
        self.test_harness.build_test_harness(assumptions)
        verifier_path = os.path.join(self.tmp_dir, TestHarness.VERIFIER_PACKAGE, 'Verifier.java')
        self.assertFileEqual(expected_output_path, verifier_path)


if __name__ == '__main__':
    unittest.main()
