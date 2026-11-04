const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const { createRequire } = require('node:module');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');

const templates = path.resolve(__dirname, '../skills/uni-rn-dev/templates/quality');
const toolsRoot = path.join(__dirname, 'fixtures/rn-quality');
const toolRequire = createRequire(path.join(toolsRoot, 'package.json'));
const { ESLint } = toolRequire('eslint');
const prettier = toolRequire('prettier');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'rn-quality-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.cpSync(templates, root, { recursive: true });
  fs.symlinkSync(path.join(toolsRoot, 'node_modules'), path.join(root, 'node_modules'), 'dir');
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.scripts.json')));
  pkg.name = 'quality-fixture';
  pkg.version = '0.0.0';
  pkg.private = true;
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify(pkg));
  fs.writeFileSync(path.join(root, 'tsconfig.json'), JSON.stringify({
    extends: './tsconfig.quality.json',
    compilerOptions: { jsx: 'react-jsx', module: 'esnext', moduleResolution: 'bundler',
      lib: ['es2022', 'dom'], skipLibCheck: true, types: ['jest'], noEmit: true },
    include: ['App.tsx', 'src/**/*.ts', '__tests__/**/*.ts'],
  }));
  fs.writeFileSync(path.join(root, 'babel.config.cjs'), "module.exports = { presets: ['@react-native/babel-preset'] };\n");
  fs.mkdirSync(path.join(root, 'src'));
  fs.mkdirSync(path.join(root, '__tests__'));
  for (const file of ['App.tsx', 'src/constants.ts', '__tests__/quality.test.ts']) fs.writeFileSync(path.join(root, file), 'export {};\n');
  const env = { ...process.env, HUSKY: '1',
    GIT_AUTHOR_NAME: 'Quality fixture', GIT_AUTHOR_EMAIL: 'quality@example.invalid',
    GIT_COMMITTER_NAME: 'Quality fixture', GIT_COMMITTER_EMAIL: 'quality@example.invalid' };
  const run = (command, args, input) => spawnSync(command, args, { cwd: root, env, input, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
  const git = args => run('git', ['-c', 'commit.gpgsign=false', ...args]);
  return { root, run, git, eslint: new ESLint({ cwd: root }), write: (file, text) => fs.writeFileSync(path.join(root, file), text) };
}

function success(result) {
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}\n${result.error || ''}`);
  return result.stdout;
}

async function lint(f, text, file = 'App.tsx') {
  const [result] = await f.eslint.lintText(text, { filePath: path.join(f.root, file) });
  assert.equal(result.fatalErrorCount, 0, JSON.stringify(result.messages));
  return result.messages;
}

test('default ESLint rejects unsafe types and control flow, with real type information', async t => {
  const f = fixture(t);
  const messages = await lint(f, `
    export function read(value: string | number, flag: boolean, other: boolean) {
      if (flag) return value as never;
      return other ? 'a' : flag ? 'b' : 'c';
    }
    export function passthrough(value: any) { return value; }
  `);
  const rules = new Set(messages.map(item => item.ruleId));
  for (const rule of ['curly', 'no-nested-ternary', '@typescript-eslint/no-explicit-any', '@typescript-eslint/no-unsafe-type-assertion']) assert.ok(rules.has(rule), rule);
  assert.deepEqual(await lint(f, `
    export function narrow(value: unknown): string {
      if (typeof value === 'string') { return value; }
      return '';
    }
    export function widen(value: string): string | number { return value as string | number; }
  `), []);
});

test('naming distinguishes constants and runtime values, keeping React and protocol names', async t => {
  const f = fixture(t);
  const naming = messages => messages.filter(item => item.ruleId === '@typescript-eslint/naming-convention');
  assert.equal(naming(await lint(f, 'export const maxCount = 1;', 'src/constants.ts')).length, 1);
  assert.deepEqual(naming(await lint(f, 'export const MAX_COUNT = 1;', 'src/constants.ts')), []);
  assert.equal(naming(await lint(f, 'export const bad_name = 1;')).length, 1);
  assert.deepEqual(naming(await lint(f, `
    import { createContext, memo } from 'react';
    import type { ComponentType } from 'react';
    export const runtimeValue = Date.now();
    export const SelectionContext = createContext('');
    export function Card() { return null; }
    export const MemoCard = memo(Card);
    export const payload = { customer_id: '1' };
    export function readCustomer(_unused: unknown, Component: ComponentType) {
      const { customer_id } = payload;
      return <Component key={customer_id} />;
    }
  `)), []);
});

test('Jest assertion and focus checks apply to cases without forbidding fixture exports', async t => {
  const f = fixture(t);
  const messages = await lint(f, "test.only('case', () => { if (Date.now()) { expect(1).toBe(1); } });", '__tests__/quality.test.ts');
  assert.ok(messages.some(item => item.ruleId === 'jest/no-conditional-expect'));
  assert.ok(messages.some(item => item.ruleId === 'jest/no-focused-tests'));
  assert.deepEqual(await lint(f, 'export function fixtureValue() { return 1; }'), []);
});

test('renamed imports follow local naming without renaming the source API', async t => {
  const f = fixture(t);
  for (const [alias, valid] of [
    ['make_memo', false], ['_memo', false], ['MEMO_', false], ['MEMO__VALUE', false], ['ǅMemo', false],
    ['createMemo', true], ['CreateMemo', true], ['CREATE_MEMO', true], ['组件', true],
  ]) {
    const messages = await lint(f, `import { memo as ${alias} } from 'react'; export const Card = ${alias}(() => null);`);
    assert.equal(messages.some(item => item.ruleId === 'rn-quality/import-alias-case'), !valid, alias);
  }
});

test('TypeScript enforces optional and indexed values while library declarations can still emit', t => {
  const f = fixture(t);
  const compiler = path.join(toolsRoot, 'node_modules/@typescript/native/bin/tsc');
  f.write('App.tsx', `export interface Options { name?: string; }
export const options: Options = { name: undefined };
const values: string[] = [];
export const first: string = values[0];
`);
  const invalid = f.run(process.execPath, [compiler, '--pretty', 'false']);
  assert.notEqual(invalid.status, 0);
  assert.match(invalid.stdout + invalid.stderr, /exactOptionalPropertyTypes/);
  assert.match(invalid.stdout + invalid.stderr, /undefined/);
  f.write('App.tsx', 'export const value: string = "ok";\n');
  f.write('tsconfig.build.json', JSON.stringify({ extends: './tsconfig.json',
    compilerOptions: { noEmit: false, declaration: true, emitDeclarationOnly: true, outDir: 'lib' } }));
  success(f.run(process.execPath, [compiler, '--project', 'tsconfig.build.json', '--pretty', 'false']));
  assert.ok(fs.existsSync(path.join(f.root, 'lib/App.d.ts')));
});

test('formatter checks multiline blocks and preserves explicit native exclusions', async t => {
  const f = fixture(t);
  const options = { ...await prettier.resolveConfig(path.join(f.root, 'App.tsx')), filepath: 'App.tsx' };
  assert.equal(await prettier.check('if (ready) { run(); }\n', options), false);
  assert.equal(await prettier.check('if (ready) {\n  run();\n}\n', options), true);
  assert.equal(await f.eslint.isPathIgnored(path.join(f.root, 'android/generated.ts')), true);
  assert.equal((await prettier.getFileInfo(path.join(f.root, 'android/generated.ts'), { ignorePath: path.join(f.root, '.prettierignore') })).ignored, true);
});

test('real Husky hooks reject violations and preserve partially staged content', t => {
  const f = fixture(t);
  f.write('.gitignore', 'node_modules/\n');
  f.write('App.tsx', 'export const initialValue = 1;\n');
  success(f.git(['init', '-q']));
  success(f.git(['add', '.']));
  success(f.git(['-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'chore: 初始化验证样例']));
  success(f.run('npm', ['run', 'prepare']));
  assert.equal(success(f.git(['config', '--get', 'core.hooksPath'])).trim(), '.husky/_');
  f.write('App.tsx', 'export const wrong_name = 1;\n');
  success(f.git(['add', 'App.tsx']));
  const invalid = f.git(['commit', '-m', 'feat: 验证命名检查']);
  assert.notEqual(invalid.status, 0);
  assert.match(invalid.stderr + invalid.stdout, /naming-convention/);
  const staged = 'export const validName = 2;\n';
  f.write('App.tsx', staged);
  success(f.git(['add', 'App.tsx']));
  const badMessage = f.git(['commit', '-m', 'feat: add value']);
  assert.notEqual(badMessage.status, 0);
  assert.match(badMessage.stderr + badMessage.stdout, /subject-chinese/);
  const unfinished = `${staged}\nexport const unfinished_name=3;\n`;
  f.write('App.tsx', unfinished);
  success(f.git(['commit', '-m', 'feat: 增加默认检查']));
  assert.equal(success(f.git(['show', 'HEAD:App.tsx'])), staged);
  assert.equal(fs.readFileSync(path.join(f.root, 'App.tsx'), 'utf8'), unfinished);
  assert.equal(success(f.git(['diff', '--cached'])), '');
  assert.equal(success(f.git(['stash', 'list'])), '');
});
