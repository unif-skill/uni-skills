'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const modulePath = path.resolve(__dirname, '../templates/scripts/organization.cjs');
const profile = {
  schemaVersion: 1, owner: 'example-org', namePattern: '^@example/widget-[a-z0-9-]+$',
  pagesURL: 'https://example-org.github.io/{repo}/', releaseAppId: 12345,
  repositorySettings: { allow_merge_commit: false, allow_squash_merge: true,
    security_and_analysis: { secret_scanning: { status: 'enabled' } } },
  security: { codeqlDefaultSetup: 'not-configured', dependabotSecurityUpdates: 'disabled', privateVulnerabilityReporting: true },
  obsoleteFiles: ['.github/dependabot.yaml', '.github/workflows/retired-check.yml'],
};
function fixture(t, value) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'delivery-organization-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, '.github'));
  if (value !== undefined) fs.writeFileSync(path.join(root, '.github/organization.json'), JSON.stringify(value));
  return root;
}
const loaders = {
  Node: (root, repository) => require(modulePath).readOrganization(root, repository),
  Python: (root, repository) => {
    const result = spawnSync('python3', ['-c',
      'import json,runpy,sys; m=runpy.run_path(sys.argv[1]); print(json.dumps(m["read_organization"](sys.argv[2], sys.argv[3] or None)))',
      path.join(__dirname, 'setup_repo.py'), root, repository || ''], {
      encoding: 'utf8', env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    });
    if (result.status !== 0) throw new Error(result.stderr);
    return JSON.parse(result.stdout);
  },
};
for (const [label, read] of Object.entries(loaders)) {
  test(`${label} reads only the project profile and permits an absent organization policy`, t => {
    assert.equal(read(fixture(t), 'other/widget'), null);
    assert.deepEqual(read(fixture(t, profile), 'example-org/widget-one'), profile);
    assert.deepEqual(read(fixture(t, { schemaVersion: 1 }), 'other/widget'), { schemaVersion: 1 });
    assert.throws(() => read(fixture(t, profile), 'other/widget'), /owner/);
  });
  test(`${label} rejects malformed organization fields and unsafe obsolete automation paths`, t => {
    for (const value of [
      [], { ...profile, schemaVersion: 2 }, { ...profile, unknownPolicy: true },
      { ...profile, owner: '../wrong' }, { ...profile, namePattern: '(' },
      { ...profile, releaseAppId: true }, { ...profile, releaseAppId: 0 },
      { ...profile, pagesURL: 'http://example.org/{repo}/' },
      { ...profile, pagesURL: 'https://user:password@example.org/{repo}/' },
      { ...profile, pagesURL: 'https://example.org/{owner}/{repo}/' },
      { ...profile, repositorySettings: { allow_merge_commit: 'false' } },
      { ...profile, repositorySettings: { visibility: 'public' } },
      { ...profile, security: { dependabotSecurityUpdates: 'unknown' } },
      { ...profile, obsoleteFiles: ['../outside'] }, { ...profile, obsoleteFiles: ['.git/config'] },
      { ...profile, obsoleteFiles: ['/tmp/file.yml'] },
      { ...profile, obsoleteFiles: ['.github/workflows/ci.yml'] },
      { ...profile, obsoleteFiles: ['.github/workflows/release.yaml'] },
      { ...profile, obsoleteFiles: ['.github/dependabot.yaml', '.github/dependabot.yaml'] },
      { ...profile, obsoleteFiles: ['.github/workflows/old\nname.yml'] },
    ]) assert.throws(() => read(fixture(t, value), 'example-org/widget-one'));
  });
  test(`${label} rejects symlinks in the organization configuration path`, t => {
    const root = fixture(t);
    const other = fixture(t, profile);
    fs.symlinkSync(path.join(other, '.github/organization.json'), path.join(root, '.github/organization.json'));
    assert.throws(() => read(root, 'example-org/widget-one'), /symlink/);
    fs.unlinkSync(path.join(root, '.github/organization.json'));
    fs.rmdirSync(path.join(root, '.github'));
    fs.symlinkSync(path.join(other, '.github'), path.join(root, '.github'));
    assert.throws(() => read(root, 'example-org/widget-one'), /symlink/);
  });
}
test('identity policies enforce the whole npm name, repository owner and Pages address', () => {
  const { validateIdentity, resolvePagesURL } = require(modulePath);
  const pkg = { name: '@example/widget-one', repository: 'git+https://github.com/example-org/widget-one.git',
    homepage: 'https://example-org.github.io/widget-one/' };
  assert.doesNotThrow(() => validateIdentity(profile, pkg));
  assert.doesNotThrow(() => validateIdentity(null, pkg));
  assert.equal(resolvePagesURL(profile, 'example-org/widget-one'), pkg.homepage);
  assert.throws(() => validateIdentity(profile, { ...pkg, name: '@another/widget-one' }), /namePattern|package name/);
  assert.throws(() => validateIdentity(profile, { ...pkg, repository: 'https://github.com/other/widget-one' }), /owner/);
  assert.throws(() => validateIdentity(profile, { ...pkg, homepage: 'https://elsewhere.example/widget-one/' }), /pagesURL|homepage/);
  assert.throws(() => validateIdentity(profile, pkg, 'example-org/other-widget'), /repository/);
});
