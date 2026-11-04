import tempfile
import unittest
from pathlib import Path

from scripts.sync_rn_quality import sync_quality


class QualityDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = self.root / 'skills/uni-rn-dev'
        (source / 'references').mkdir(parents=True)
        (source / 'references/quality.md').write_text('# Quality\n')
        (source / 'templates/quality/.husky').mkdir(parents=True)
        (source / 'templates/quality/eslint.config.cjs').write_text('module.exports = [];\n')
        (source / 'templates/quality/.husky/pre-commit').write_text('npm run lint:staged\n')

    def test_copies_are_self_contained_and_check_does_not_write(self):
        with self.assertRaises(ValueError):
            sync_quality(self.root, check=True)
        sync_quality(self.root)
        for skill in ['uni-github-delivery', 'uni-rn-library']:
            target = self.root / 'skills' / skill
            self.assertEqual((target / 'templates/quality/.husky/pre-commit').read_text(), 'npm run lint:staged\n')
            (target / 'SKILL.md').write_text('Project entry\n')
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        sync_quality(self.root, check=True)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_changed_or_missing_asset_fails_until_synced(self):
        sync_quality(self.root)
        target = self.root / 'skills/uni-github-delivery/templates/quality/eslint.config.cjs'
        target.write_text('changed\n')
        with self.assertRaisesRegex(ValueError, 'eslint.config.cjs'):
            sync_quality(self.root, check=True)
        self.assertEqual(target.read_text(), 'changed\n')
        sync_quality(self.root)
        sync_quality(self.root, check=True)
        target.unlink()
        with self.assertRaises(ValueError):
            sync_quality(self.root, check=True)

    def test_symlink_cannot_redirect_generated_output(self):
        target = self.root / 'skills/uni-github-delivery'
        target.mkdir(parents=True)
        outside = self.root / 'outside'
        outside.mkdir()
        (target / 'templates').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            sync_quality(self.root)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
