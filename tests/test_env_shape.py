import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/uni-code-change/scripts/check_env_shape.py'


class EnvShapeTests(unittest.TestCase):
    def check(self, template: str, candidate: str, layout: str | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _ = (root / 'template').write_text(template)
            _ = (root / 'candidate').write_text(candidate)
            args = [sys.executable, str(SCRIPT), str(root / 'template'), str(root / 'candidate')]
            if layout is not None:
                _ = (root / 'layout').write_text(layout)
                args.extend(['--layout-from', str(root / 'layout')])
            before = (root / 'candidate').read_bytes()
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual((root / 'candidate').read_bytes(), before)
            return result

    def test_values_may_differ_when_names_order_and_layout_match(self) -> None:
        result = self.check('DB=example\nKEY=\n', '# storage\nDB=localhost\nKEY=FAKE_SECRET\n', '# storage\nDB=remote\nKEY=other\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('FAKE_SECRET', result.stdout + result.stderr)

    def test_partial_override_does_not_pass_as_complete_profile(self) -> None:
        result = self.check('AUTH=\nDB=\nREDIS=\n', 'DB=local\nREDIS=local\n')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('AUTH', result.stdout)

    def test_order_and_grouping_are_checked_separately(self) -> None:
        reordered = self.check('AUTH=\nDB=\n', 'DB=local\nAUTH=FAKE_SECRET\n')
        self.assertEqual(reordered.returncode, 1)
        regrouped = self.check('AUTH=\nDB=\n', '# auth\nAUTH=x\nDB=y\n', '# auth\nAUTH=x\n\n# storage\nDB=y\n')
        self.assertEqual(regrouped.returncode, 1)
        self.assertNotIn('FAKE_SECRET', reordered.stdout + reordered.stderr)

    def test_duplicate_and_extra_keys_are_reported_without_values(self) -> None:
        result = self.check('A=\n', 'A=FAKE_SECRET_ONE\nA=FAKE_SECRET_TWO\nEXTRA=FAKE_SECRET_THREE\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('EXTRA', result.stdout)
        self.assertIn('A', result.stdout)
        self.assertNotIn('FAKE_SECRET', result.stdout + result.stderr)

    def test_assignment_like_text_inside_multiline_value_is_not_a_key(self) -> None:
        result = self.check('CERT=\nDB=\n', 'CERT="first\nFAKE_SECRET=inside\nlast"\nDB=local\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('FAKE_SECRET', result.stdout + result.stderr)

    def test_invalid_input_does_not_echo_secret_lines(self) -> None:
        for candidate in ['A="FAKE_SECRET\n', 'FAKE_SECRET_INVALID_LINE\n']:
            result = self.check('A=\n', candidate)
            self.assertEqual(result.returncode, 2)
            self.assertIn('error', result.stdout)
            self.assertNotIn('FAKE_SECRET', result.stdout + result.stderr)


if __name__ == '__main__':
    _ = unittest.main()
