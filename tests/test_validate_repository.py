import json
import tempfile
import unittest
from pathlib import Path

from scripts.sync_release_tools import FILES, sync_release_tools
from scripts.validate_repository import validate_repository


class ValidateRepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        source = self.base / 'source'
        for name in FILES:
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# shared release implementation\n')
        sync_release_tools(source, self.root)
        (self.root / 'assets').mkdir()
        (self.root / 'assets/logo.png').write_bytes(b'logo')
        self.manifest = {
            'name': 'uni-skills', 'version': '0.4.4',
            'extensions': {'com.openai': {'interface': {'logo': './assets/logo.png'}}},
        }
        self.write_manifest()
        self.marketplace = self.root / '.agents/plugins/marketplace.json'
        self.marketplace.parent.mkdir(parents=True)
        self.marketplace.write_text(json.dumps({'name': 'uni-skills', 'plugins': [
            {'name': 'uni-skills', 'source': {'source': 'local', 'path': './'}}]}))
        self.skill = self.root / 'skills/uni-example'
        (self.skill / 'agents').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('---\nname: uni-example\ndescription: Example\n---\n')
        (self.skill / 'agents/openai.yaml').write_text('interface:\n  display_name: Example\n')

    def write_manifest(self):
        (self.root / 'plugin.json').write_text(json.dumps(self.manifest))

    def test_valid_candidate_uses_its_exact_manifest_version_and_local_snapshot(self):
        self.assertEqual(validate_repository(self.root, release_tag='v0.4.4'), 1)
        with self.assertRaises(ValueError):
            validate_repository(self.root, release_tag='v0.4.5')

    def test_manifest_identity_and_stable_version_are_required(self):
        for key, value in [('name', 'another-plugin'), ('version', '0.04.4'),
                           ('version', 'v0.4.4'), ('version', '0.4.4-beta.1')]:
            with self.subTest(key=key, value=value):
                original = self.manifest[key]
                self.manifest[key] = value
                self.write_manifest()
                with self.assertRaises(ValueError):
                    validate_repository(self.root)
                self.manifest[key] = original

    def test_broken_asset_or_skill_entry_prevents_release(self):
        for path in (self.root / 'assets/logo.png', self.skill / 'SKILL.md', self.skill / 'agents/openai.yaml'):
            with self.subTest(path=path):
                content = path.read_bytes()
                path.unlink()
                with self.assertRaises(ValueError):
                    validate_repository(self.root)
                path.write_bytes(content)

    def test_marketplace_cannot_redirect_to_another_plugin(self):
        self.marketplace.write_text(json.dumps({'name': 'uni-skills', 'plugins': [
            {'name': 'uni-skills', 'source': {'source': 'github', 'path': './'}}]}))
        with self.assertRaises(ValueError):
            validate_repository(self.root)

    def test_assets_cannot_escape_repository(self):
        (self.base / 'outside.png').write_bytes(b'outside')
        self.manifest['extensions']['com.openai']['interface']['logo'] = '../outside.png'
        self.write_manifest()
        with self.assertRaises(ValueError):
            validate_repository(self.root)

    def test_malformed_plugin_interface_is_rejected(self):
        for extensions in (None, [], {'com.openai': None}, {'com.openai': {'interface': []}}):
            with self.subTest(extensions=extensions):
                self.manifest['extensions'] = extensions
                self.write_manifest()
                with self.assertRaises(ValueError):
                    validate_repository(self.root)

    def test_release_tool_drift_prevents_candidate_validation(self):
        (self.root / FILES[0]).write_text('# changed release behavior\n')
        with self.assertRaises(ValueError):
            validate_repository(self.root)


if __name__ == '__main__':
    unittest.main()
