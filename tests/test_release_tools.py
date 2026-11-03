import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.sync_release_tools import FILES, check_release_tools, sync_release_tools


class ReleaseToolsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base / 'source'
        self.target = self.base / 'target'
        self.target.mkdir()
        for name in FILES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'# shared {name}\n')

    def test_sync_copies_fixed_tools_and_tests_without_other_source_files(self):
        (self.source / 'plugin.json').write_text('{"name":"must-not-copy"}')
        unrelated = self.target / 'notes.md'
        unrelated.write_text('keep project work\n')
        sync_release_tools(self.source, self.target)
        check_release_tools(self.target)
        for name in FILES:
            self.assertEqual((self.target / name).read_bytes(), (self.source / name).read_bytes())
        self.assertFalse((self.target / 'plugin.json').exists())
        self.assertEqual(unrelated.read_text(), 'keep project work\n')
        record = json.loads((self.target / 'scripts/release-tools.json').read_text())
        self.assertEqual(set(record['files']), set(FILES))
        for name, digest in record['files'].items():
            self.assertEqual(digest, hashlib.sha256((self.source / name).read_bytes()).hexdigest())

    def test_check_is_read_only_and_distinguishes_adopted_snapshot_from_new_source(self):
        sync_release_tools(self.source, self.target)
        before = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        (self.source / FILES[0]).write_text('# upstream improvement\n')
        check_release_tools(self.target)
        with self.assertRaises(ValueError):
            sync_release_tools(self.source, self.target, check=True)
        after = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        sync_release_tools(self.source, self.target)
        check_release_tools(self.target)

    def test_local_drift_is_rejected_in_ci_and_not_overwritten_by_sync(self):
        sync_release_tools(self.source, self.target)
        changed = self.target / FILES[0]
        changed.write_text('# unrelated local work\n')
        with self.assertRaises(ValueError):
            check_release_tools(self.target)
        with self.assertRaises(ValueError):
            sync_release_tools(self.source, self.target)
        self.assertEqual(changed.read_text(), '# unrelated local work\n')

    def test_first_sync_does_not_overwrite_unmanaged_file(self):
        path = self.target / FILES[0]
        path.parent.mkdir()
        path.write_text('# existing project file\n')
        with self.assertRaises(ValueError):
            sync_release_tools(self.source, self.target)
        self.assertFalse((self.target / 'scripts/release-tools.json').exists())
        self.assertEqual(path.read_text(), '# existing project file\n')

    def test_missing_source_fails_before_writing_any_target(self):
        (self.source / FILES[-1]).unlink()
        with self.assertRaises((ValueError, OSError)):
            sync_release_tools(self.source, self.target)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_symlink_cannot_redirect_managed_writes(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.target / 'scripts').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            sync_release_tools(self.source, self.target)
        self.assertEqual(list(outside.iterdir()), [])

    def test_record_requires_exact_file_set_and_valid_hashes(self):
        sync_release_tools(self.source, self.target)
        path = self.target / 'scripts/release-tools.json'
        original = json.loads(path.read_text())
        for files in ({}, {**original['files'], '../outside': 'a' * 64},
                      {**original['files'], FILES[0]: 'not-a-digest'}):
            with self.subTest(files=files):
                path.write_text(json.dumps({**original, 'files': files}))
                with self.assertRaises(ValueError):
                    check_release_tools(self.target)


if __name__ == '__main__':
    unittest.main()
