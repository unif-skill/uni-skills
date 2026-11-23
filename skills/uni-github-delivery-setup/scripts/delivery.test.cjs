const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'github-delivery-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: '@example/widget', version: '0.1.0', description: 'Fixture library',
    homepage: 'https://example.github.io/widget/', repository: 'https://github.com/example/widget',
    license: 'MIT', private: true, files: ['lib'], main: 'lib/index.js', types: 'lib/index.d.ts',
    exports: { '.': { types: './lib/index.d.ts', default: './lib/index.js' } },
    scripts: { lint: 'eslint . --max-warnings=0', typecheck: 'tsc --noEmit', 'check:format': 'prettier --check .',
      'lint:staged': 'lint-staged', commitlint: 'commitlint', prepare: 'husky' },
    devDependencies: { turbo: '1', '@release-it/conventional-changelog': '1', husky: '9.1.7',
      'lint-staged': '16.4.0', '@commitlint/cli': '21.2.4', '@commitlint/config-conventional': '21.2.4' },
    'release-it': { npm: { publish: true, skipChecks: true } },
  }));
  fs.writeFileSync(path.join(root, 'README.md'), '# Widget\n');
  return root;
}
function sync(root, ...flags) {
  return spawnSync('bash', [path.join(__dirname, 'sync-repo.sh'), ...flags, 'example/widget', root], { encoding: 'utf8' });
}
function verify(root) {
  return spawnSync(process.execPath, [path.join(root, '.github/scripts/check-delivery.cjs'), root], { encoding: 'utf8' });
}
function ok(result) { assert.equal(result.status, 0, result.stdout + result.stderr); }
function snapshot(root) {
  return fs.readdirSync(root, { recursive: true }).sort().filter(file => fs.statSync(path.join(root, file)).isFile())
    .map(file => [file, fs.readFileSync(path.join(root, file), 'utf8')]);
}

test('new non-Unif library adopts self-contained CI without enabling PR model service', t => {
  const root = fixture(t);
  ok(sync(root));
  ok(verify(root));
  const ci = fs.readFileSync(path.join(root, '.github/workflows/ci.yml'), 'utf8');
  assert.match(ci, /node \.github\/scripts\/check-delivery\.cjs/);
  assert.doesNotMatch(ci, /unif-design\/\.github|Checkout organization standards/);
  assert.equal(fs.existsSync(path.join(root, '.github/workflows/pr-agent.yml')), false);
  assert.equal(fs.existsSync(path.join(root, 'lefthook.yml')), false);
  assert.match(fs.readFileSync(path.join(root, '.husky/pre-commit'), 'utf8'), /yarn lint:staged/);
  assert.match(fs.readFileSync(path.join(root, '.husky/commit-msg'), 'utf8'), /commitlint --edit/);
  assert.match(ci, /yarn check:format/);
  const before = snapshot(root);
  ok(sync(root, '--check'));
  assert.deepEqual(snapshot(root), before);
  ok(sync(root));
  assert.deepEqual(snapshot(root), before);
  const workflows = fs.readdirSync(path.join(root, '.github/workflows')).map(file => path.join(root, '.github/workflows', file));
  ok(spawnSync('actionlint', ['-shellcheck=shellcheck', ...workflows], { cwd: root, encoding: 'utf8' }));
});

test('offline checker preserves drift, adopted obsolete automation and dependency gates', t => {
  const root = fixture(t);
  fs.mkdirSync(path.join(root, '.github'));
  fs.writeFileSync(path.join(root, '.github/organization.json'), JSON.stringify({ schemaVersion: 1, owner: 'example', obsoleteFiles: ['.github/dependabot.yaml'] }));
  ok(sync(root));
  const ciPath = path.join(root, '.github/workflows/ci.yml');
  const ci = fs.readFileSync(ciPath);
  fs.appendFileSync(ciPath, '\n# drift\n');
  assert.notEqual(verify(root).status, 0);
  fs.writeFileSync(ciPath, ci);
  fs.writeFileSync(path.join(root, '.github/dependabot.yaml'), 'version: 2\n');
  assert.notEqual(verify(root).status, 0);
  fs.unlinkSync(path.join(root, '.github/dependabot.yaml'));
  const pkgPath = path.join(root, 'package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath));
  delete pkg.devDependencies.turbo;
  fs.writeFileSync(pkgPath, JSON.stringify(pkg));
  assert.match(verify(root).stderr, /turbo/);
});

test('existing Lefthook guards remain intact and Husky is not added', t => {
  const root = fixture(t);
  const guards = 'pre-commit:\n  commands:\n    branch-and-native:\n      run: node scripts/project-guards.cjs\n';
  fs.writeFileSync(path.join(root, 'lefthook.yml'), guards);
  ok(sync(root));
  assert.equal(fs.readFileSync(path.join(root, 'lefthook.yml'), 'utf8'), guards);
  assert.equal(fs.existsSync(path.join(root, '.husky')), false);
  assert.equal(JSON.parse(fs.readFileSync(path.join(root, '.github/delivery.json'))).hooks, 'lefthook');
  ok(sync(root, '--check'));
});

test('existing Husky tasks and inline commit conventions are preserved', t => {
  const root = fixture(t);
  fs.mkdirSync(path.join(root, '.husky'));
  const preCommit = 'node scripts/branch-guard.cjs\nyarn lint:staged\nyarn native:check\n';
  fs.writeFileSync(path.join(root, '.husky/pre-commit'), preCommit);
  const pkgPath = path.join(root, 'package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath));
  pkg.scripts.prepare = 'bob build && husky';
  pkg['lint-staged'] = { '*.ts': ['eslint --max-warnings=0', 'prettier --check'] };
  pkg.commitlint = { extends: ['@commitlint/config-conventional'] };
  fs.writeFileSync(pkgPath, JSON.stringify(pkg));
  const originalPackage = fs.readFileSync(pkgPath);
  ok(sync(root));
  assert.equal(fs.readFileSync(path.join(root, '.husky/pre-commit'), 'utf8'), preCommit);
  assert.deepEqual(fs.readFileSync(pkgPath), originalPackage);
  assert.equal(fs.existsSync(path.join(root, 'lint-staged.config.cjs')), false);
  assert.equal(fs.existsSync(path.join(root, 'commitlint.config.cjs')), false);
  ok(sync(root, '--check'));
});

test('missing quality scripts fail adoption without inventing successful commands', t => {
  const root = fixture(t);
  const file = path.join(root, 'package.json');
  const pkg = JSON.parse(fs.readFileSync(file));
  delete pkg.scripts['check:format'];
  fs.writeFileSync(file, JSON.stringify(pkg));
  const before = fs.readFileSync(file);
  const result = sync(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /Missing quality script: check:format/);
  assert.deepEqual(fs.readFileSync(file), before);
});

test('ambiguous hook managers fail before writing project files', t => {
  const root = fixture(t);
  fs.mkdirSync(path.join(root, '.husky'));
  fs.writeFileSync(path.join(root, '.husky/pre-commit'), 'yarn lint:staged\n');
  fs.writeFileSync(path.join(root, 'lefthook.yml'), 'pre-commit: {}\n');
  const before = snapshot(root);
  const result = sync(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Multiple Git hook managers/);
  assert.deepEqual(snapshot(root), before);
});

test('receipt hashes the managed Agent block and preserves project-owned text', t => {
  const root = fixture(t);
  ok(sync(root));
  const agents = path.join(root, 'AGENTS.md');
  fs.appendFileSync(agents, '\n## Project policy\nKeep this.\n');
  ok(verify(root));
  fs.writeFileSync(agents, fs.readFileSync(agents, 'utf8').replace('## 开发入口', '## Changed entry'));
  assert.match(verify(root).stderr, /AGENTS/);
});

test('resynchronization migrates the previous standard without losing project settings', t => {
  const root = fixture(t);
  ok(sync(root));
  const file = path.join(root, '.github/delivery.json');
  const receipt = JSON.parse(fs.readFileSync(file, 'utf8'));
  receipt.standard = 'github-delivery/react-native';
  receipt.requiredChecks.push('project-check');
  fs.writeFileSync(file, JSON.stringify(receipt));
  fs.appendFileSync(path.join(root, 'AGENTS.md'), '\n## Project policy\nKeep this.\n');
  assert.notEqual(verify(root).status, 0);
  ok(sync(root));
  const migrated = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.equal(migrated.standard, 'uni-github-delivery/rn');
  assert.deepEqual(migrated.requiredChecks, receipt.requiredChecks);
  assert.deepEqual(migrated.projectFiles, receipt.projectFiles);
  assert.match(fs.readFileSync(path.join(root, 'AGENTS.md'), 'utf8'), /Keep this\./);
  ok(verify(root));
  ok(sync(root, '--check'));
});

test('receipt rejects escaping paths, symlinks and missing managed checks', t => {
  const root = fixture(t);
  ok(sync(root));
  const receiptPath = path.join(root, '.github/delivery.json');
  const receipt = JSON.parse(fs.readFileSync(receiptPath));
  receipt.files['../../outside'] = '0'.repeat(64);
  fs.writeFileSync(receiptPath, JSON.stringify(receipt));
  assert.match(verify(root).stderr, /unsafe|path/);
  delete receipt.files['../../outside'];
  delete receipt.files['.github/scripts/check-library.cjs'];
  fs.writeFileSync(receiptPath, JSON.stringify(receipt));
  assert.notEqual(verify(root).status, 0);
});

test('removing a required action from the receipt cannot bypass template validation', t => {
  const root = fixture(t);
  ok(sync(root));
  const file = path.join(root, '.github/delivery.json');
  const receipt = JSON.parse(fs.readFileSync(file));
  delete receipt.files['.github/actions/setup/action.yml'];
  fs.writeFileSync(file, JSON.stringify(receipt));
  assert.match(verify(root).stderr, /Missing managed check/);
});

test('project overrides cannot exempt the validator and check mode never refreshes adoption', t => {
  const root = fixture(t);
  ok(sync(root));
  const file = path.join(root, '.github/delivery.json');
  const receipt = JSON.parse(fs.readFileSync(file));
  receipt.projectFiles = ['.github/scripts/check-library.cjs'];
  fs.writeFileSync(file, JSON.stringify(receipt));
  const before = snapshot(root);
  assert.notEqual(sync(root).status, 0);
  assert.deepEqual(snapshot(root), before);
});

test('project CI keeps existing jobs and must retain the offline check', t => {
  const root = fixture(t);
  ok(sync(root));
  const file = path.join(root, '.github/delivery.json');
  const receipt = JSON.parse(fs.readFileSync(file));
  receipt.projectFiles = ['.github/workflows/ci.yml'];
  fs.writeFileSync(file, JSON.stringify(receipt));
  const ciPath = path.join(root, '.github/workflows/ci.yml');
  const ci = fs.readFileSync(ciPath, 'utf8') + '\n  project-check:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo project\n';
  fs.writeFileSync(ciPath, ci);
  ok(sync(root));
  assert.equal(fs.readFileSync(ciPath, 'utf8'), ci);
  ok(verify(root));
  fs.writeFileSync(ciPath, ci.replace('run: node .github/scripts/check-delivery.cjs', 'run: echo skipped'));
  assert.notEqual(sync(root).status, 0);
});

test('new native library with a website gets its applicable checks and generic identity', t => {
  const root = fixture(t);
  fs.mkdirSync(path.join(root, 'ios'));
  fs.writeFileSync(path.join(root, 'ios/Widget.m'), '// Native source\n');
  fs.writeFileSync(path.join(root, 'widget.podspec'), '# Fixture\n');
  fs.mkdirSync(path.join(root, 'website/scripts'), { recursive: true });
  fs.writeFileSync(path.join(root, 'website/scripts/build-llms.test.js'), '// Project checks\n');
  fs.writeFileSync(path.join(root, 'website/package.json'), JSON.stringify({
    name: '@example/widget-website', scripts: { build: 'node scripts/build-llms.js', typecheck: 'tsc' },
  }));
  const pkgPath = path.join(root, 'package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath));
  pkg.workspaces = ['website'];
  fs.writeFileSync(pkgPath, JSON.stringify(pkg));
  ok(sync(root));
  ok(verify(root));
  for (const name of ['native-lint.yml', 'nightly-build-check.yml', 'deploy-docs.yml']) {
    assert.ok(fs.existsSync(path.join(root, '.github/workflows', name)));
  }
  const before = snapshot(root);
  ok(sync(root, '--check'));
  assert.deepEqual(snapshot(root), before);
});

test('a symlinked workflow directory is rejected before overwriting outside files', t => {
  const root = fixture(t);
  const outside = fixture(t);
  fs.mkdirSync(path.join(root, '.github'));
  fs.symlinkSync(outside, path.join(root, '.github/workflows'));
  const before = snapshot(outside);
  assert.notEqual(sync(root).status, 0);
  assert.deepEqual(snapshot(outside), before);
});

test('without organization configuration an explicit repository must match package identity', t => {
  const root = fixture(t);
  const before = snapshot(root);
  const result = spawnSync('bash', [path.join(__dirname, 'sync-repo.sh'), 'different-owner/other', root], { encoding: 'utf8' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /repository/);
  assert.deepEqual(snapshot(root), before);
});

test('a dangling SECURITY symlink cannot create an external file', t => {
  const root = fixture(t);
  const outside = fixture(t);
  const destination = path.join(outside, 'unexpected.md');
  fs.symlinkSync(destination, path.join(root, 'SECURITY.md'));
  const result = sync(root);
  assert.notEqual(result.status, 0);
  assert.equal(fs.existsSync(destination), false);
  assert.match(result.stderr, /symlink/);
});

test('PR service is explicit and calls only a repository-local reusable workflow', t => {
  const root = fixture(t);
  ok(sync(root, '--pr-agent'));
  const caller = fs.readFileSync(path.join(root, '.github/workflows/pr-agent.yml'), 'utf8');
  assert.match(caller, /uses: \.\/\.github\/workflows\/pr-agent-reusable\.yml/);
  assert.ok(fs.existsSync(path.join(root, '.github/workflows/pr-agent-reusable.yml')));
  ok(verify(root));
});
