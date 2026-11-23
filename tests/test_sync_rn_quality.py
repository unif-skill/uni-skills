import tempfile
import unittest
from pathlib import Path

from scripts.sync_rn_quality import sync_quality


class QualityDistributionTests(unittest.TestCase):
    def prepare_root(self) -> Path:
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        source = root / 'skills/uni-rn-dev'
        (source / 'references').mkdir(parents=True)
        _ = (source / 'references/quality.md').write_text('# Quality\n')
        (source / 'templates/quality/.husky').mkdir(parents=True)
        _ = (source / 'templates/quality/eslint.config.cjs').write_text('module.exports = [];\n')
        _ = (source / 'templates/quality/.husky/pre-commit').write_text('npm run lint:staged\n')
        return root

    def test_copies_are_self_contained_and_check_does_not_write(self) -> None:
        root = self.prepare_root()
        with self.assertRaises(ValueError):
            _ = sync_quality(root, check=True)
        _ = sync_quality(root)
        for skill in ['uni-github-delivery-setup', 'uni-rn-library']:
            target = root / 'skills' / skill
            self.assertEqual((target / 'templates/quality/.husky/pre-commit').read_text(), 'npm run lint:staged\n')
            _ = (target / 'SKILL.md').write_text('Project entry\n')
        before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        _ = sync_quality(root, check=True)
        self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_changed_or_missing_asset_fails_until_synced(self) -> None:
        root = self.prepare_root()
        _ = sync_quality(root)
        target = root / 'skills/uni-github-delivery-setup/templates/quality/eslint.config.cjs'
        _ = target.write_text('changed\n')
        with self.assertRaisesRegex(ValueError, 'eslint.config.cjs'):
            _ = sync_quality(root, check=True)
        self.assertEqual(target.read_text(), 'changed\n')
        _ = sync_quality(root)
        _ = sync_quality(root, check=True)
        target.unlink()
        with self.assertRaises(ValueError):
            _ = sync_quality(root, check=True)

    def test_symlink_cannot_redirect_generated_output(self) -> None:
        root = self.prepare_root()
        target = root / 'skills/uni-github-delivery-setup'
        target.mkdir(parents=True)
        outside = root / 'outside'
        outside.mkdir()
        (target / 'templates').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            _ = sync_quality(root)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    _ = unittest.main()
