const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const template = fs.readFileSync(path.join(__dirname, '../templates/workflows/release.yml'), 'utf8');
const step = template.split('      - name: Release\n')[1]?.split('\n      - name: ')[0];
const run = step?.split('        run: |\n')[1];
assert.ok(run, 'Release step must expose its actual run script');
const script = run.split('\n').map(line => line.replace(/^          /, '')).join('\n');

// 执行真实模板脚本；只替换会查询注册表、提交或发布的 npx 边界。
function release(t, {
  event = 'push', increment = 'auto', current = '1.2.3', next = '1.2.4\n',
  discoveryStatus = 0, publicationStatus = 0,
} = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'delivery-release-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({ name: 'release-fixture', version: current }));
  const bin = path.join(root, 'bin');
  fs.mkdirSync(bin);
  const calls = path.join(root, 'calls.jsonl');
  fs.writeFileSync(calls, '');
  fs.writeFileSync(path.join(bin, 'npx'), [
    '#!' + process.execPath,
    "const fs = require('node:fs');",
    'const args = process.argv.slice(2);',
    "if (args[0] !== 'release-it') throw new Error('Unexpected command');",
    "fs.appendFileSync(process.env.CALL_LOG, JSON.stringify(args) + '\\n');",
    "if (args.includes('--release-version')) {",
    '  process.stdout.write(process.env.NEXT_VERSION);',
    "  if (process.env.DISCOVERY_STATUS !== '0') process.stderr.write('version discovery failed\\n');",
    '  process.exit(Number(process.env.DISCOVERY_STATUS));',
    '}',
    'process.exit(Number(process.env.PUBLICATION_STATUS));',
    '',
  ].join('\n'), { mode: 0o755 });
  const result = spawnSync('bash', ['-e', '-o', 'pipefail', '-c', script], {
    cwd: root, encoding: 'utf8', timeout: 10000,
    env: {
      PATH: [bin, path.dirname(process.execPath), '/usr/bin', '/bin'].join(path.delimiter),
      EVENT_NAME: event, INCREMENT: increment, NEXT_VERSION: next,
      DISCOVERY_STATUS: String(discoveryStatus), PUBLICATION_STATUS: String(publicationStatus),
      CALL_LOG: calls,
    },
  });
  assert.ifError(result.error);
  return {
    ...result,
    calls: fs.readFileSync(calls, 'utf8').trim().split('\n').filter(Boolean).map(line => JSON.parse(line)),
  };
}

function assertStopped(result) {
  const output = result.stdout + result.stderr;
  assert.notEqual(result.status, 0, 'Release must stop: ' + output);
  assert.equal(result.calls.filter(args => !args.includes('--release-version')).length, 0,
    'Publication must not start: ' + JSON.stringify(result.calls));
}

for (const event of ['push', 'workflow_dispatch']) {
  test(event + ' auto rejects a major increase', t => {
    assertStopped(release(t, { event, next: '2.0.0\n' }));
  });

  for (const next of ['1.2.4', '1.3.0', '1.3.0-rc.1+build.01']) {
    test(event + ' auto publishes the verified version ' + next, t => {
      const result = release(t, { event, next: next + '\n' });
      assert.equal(result.status, 0, result.stdout + result.stderr);
      assert.deepEqual(result.calls, [
        ['release-it', '--release-version', '--ci'],
        ['release-it', next, '--ci'],
      ]);
    });
  }

  for (const next of ['', '1.2.4\n']) {
    test(event + ' auto rejects failed discovery even when output is ' + JSON.stringify(next), t => {
      const result = release(t, { event, next, discoveryStatus: 1 });
      assertStopped(result);
      assert.match(result.stderr, /version discovery failed/);
    });
  }

  for (const next of ['', ' \n', 'not-a-version\n', '1.2.4oops\n', '1.2.4.5\n',
    '01.2.4\n', '1.02.4\n', '1.2.04\n', '1.2.4-01\n', '1.2.4-rc..1\n',
    '1.2.4+build..1\n', 'diagnostic\n1.2.4\n']) {
    test(event + ' auto rejects empty or malformed candidate ' + JSON.stringify(next), t => {
      assertStopped(release(t, { event, next }));
    });
  }

  for (const current of ['', '1.2', '1.2.3oops', '01.2.3', '1.2.3-01']) {
    test(event + ' auto rejects malformed current version ' + JSON.stringify(current), t => {
      assertStopped(release(t, { event, current }));
    });
  }
}

for (const increment of ['patch', 'minor', 'major']) {
  test('manual explicit ' + increment + ' keeps the requested release type', t => {
    const result = release(t, { event: 'workflow_dispatch', increment });
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.deepEqual(result.calls, [['release-it', increment, '--ci']]);
  });
}

test('a push cannot authorize an explicit major release', t => {
  assertStopped(release(t, { increment: 'major' }));
});

test('an unsupported manual increment cannot bypass the version guard', t => {
  assertStopped(release(t, { event: 'workflow_dispatch', increment: '2.0.0' }));
});

test('a failure to publish the verified version remains a failure', t => {
  const result = release(t, { publicationStatus: 1 });
  assert.notEqual(result.status, 0);
  assert.deepEqual(result.calls.at(-1), ['release-it', '1.2.4', '--ci']);
});
