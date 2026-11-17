"""Finite source-boundary tests; they do not substitute for R2U2 execution."""

import unittest

from r2u2_native_replay import (
    compiler_command,
    expected_and_observed,
    make_corrected,
    make_trace,
    native_spec11_at_time1,
    source_bindings,
)


EXCERPT = """INPUT
    Battery_Cell_Temp_1, Battery_Cell_Temp_2, Battery_Cell_Temp_3, Battery_Cell_Temp_4: float;
DEFINE
    Battery_Cell_Temp_1_RC_LT_1 := abs(Battery_Cell_Temp_1 - prev(22.0, Battery_Cell_Temp_1)) < 1.0;
    Battery_Cell_Temp_2_RC_LT_1 := abs(Battery_Cell_Temp_1 - prev(22.0, Battery_Cell_Temp_2)) < 1.0;
    Battery_Cell_Temp_3_RC_LT_1 := abs(Battery_Cell_Temp_1 - prev(22.0, Battery_Cell_Temp_3)) < 1.0;
    Battery_Cell_Temp_4_RC_LT_1 := abs(Battery_Cell_Temp_1 - prev(22.0, Battery_Cell_Temp_4)) < 1.0;
FTSPEC
    SPEC11: Battery_Cell_Temp_1_RC_LT_1 && Battery_Cell_Temp_2_RC_LT_1 && Battery_Cell_Temp_3_RC_LT_1 && Battery_Cell_Temp_4_RC_LT_1;
"""


class CySatBoundaryTests(unittest.TestCase):
    def test_dependency_fingerprint_exposes_three_cross_channel_terms(self):
        self.assertEqual(source_bindings(EXCERPT), ((1, 1), (1, 2), (1, 3), (1, 4)))

    def test_minimal_repair_changes_only_current_sensor_operand(self):
        amended = make_corrected(EXCERPT)
        self.assertEqual(source_bindings(amended), ((1, 1), (2, 2), (3, 3), (4, 4)))
        self.assertEqual(amended.count("SPEC11:"), 1)
        self.assertEqual(amended.count("prev(22.0,"), 4)

    def test_missed_jump_and_false_alarm(self):
        controls = [
            ((22, 22, 22, 22), (22, 22, 22, 22), (True, True)),
            ((22, 22, 22, 22), (22, 25, 22, 22), (False, True)),
            ((25, 22, 22, 22), (25, 22, 22, 22), (True, False)),
        ]
        for prior, current, result in controls:
            self.assertEqual(expected_and_observed(EXCERPT, prior, current), result)
            self.assertEqual(expected_and_observed(make_corrected(EXCERPT), prior, current), (result[0], result[0]))

    def test_two_sample_csv_has_stable_header_and_channel_values(self):
        header = "# Other,Battery_Cell_Temp_1,Battery_Cell_Temp_2,Battery_Cell_Temp_3,Battery_Cell_Temp_4\n"
        first_data = "99,12,13,14,15\n"
        trace = make_trace(header, first_data, (22, 22, 22, 22), (22, 25, 22, 22))
        self.assertEqual(trace.splitlines(), [
            header.strip(),
            "99,22.0,22.0,22.0,22.0",
            "99,22.0,25.0,22.0,22.0",
        ])

    def test_float_signal_compilation_requires_c2po_booleanizer(self):
        command = compiler_command("r2u2", "official.c2po", "eps.csv", "official.bin")
        self.assertEqual(command[0:2], ["python3", "r2u2/compiler/c2po.py"])
        self.assertIn("--booleanizer", command)
        self.assertEqual(command[-6:], ["--spec", "official.c2po", "--trace", "eps.csv", "--output", "official.bin"])

    def test_native_spec11_must_have_unambiguous_time_one_verdict(self):
        self.assertFalse(native_spec11_at_time1("10:0,T\n10:1,F\n"))
        self.assertTrue(native_spec11_at_time1("10:1,T\n10:0,F\n"))
        with self.assertRaisesRegex(ValueError, "one SPEC11"):
            native_spec11_at_time1("10:0,T\n")
        with self.assertRaisesRegex(ValueError, "one SPEC11"):
            native_spec11_at_time1("10:1,T\n10:1,F\n")


if __name__ == "__main__":
    unittest.main()
