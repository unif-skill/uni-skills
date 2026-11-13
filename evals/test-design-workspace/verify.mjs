import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import test from 'node:test';

const project = process.argv[2];
if (!project) throw new Error('用法：node verify.mjs <被测工程目录>');
const { openDrafts } = await import(pathToFileURL(resolve(project, 'src/drafts.mts')).href);

test('编辑器只接受含字符串正文的输入，错误不覆盖原草稿', () => {
  const records = new Map();
  const drafts = openDrafts('lin', records, async () => 'R1');
  drafts.edit({ body: '周四取件' });
  const expected = { owner: 'lin', body: '周四取件', receipt: null };
  for (const invalid of [{ replacement: '其他内容' }, { body: 3 }]) {
    assert.throws(() => drafts.edit(invalid), TypeError);
    assert.deepEqual(drafts.read(), expected);
  }
  assert.deepEqual(openDrafts('lin', records, async () => 'R1').read(), expected);
});

test('升级用户从原有账号打开上版离线草稿', async () => {
  const raw = await readFile(new URL('./project/samples/upgrade-v1.json', import.meta.url), 'utf8');
  const records = new Map([['mei', raw]]);
  const drafts = openDrafts('lin', records, async () => 'R1');
  assert.deepEqual(drafts.read(), { owner: 'lin', body: '', receipt: null });
  drafts.select('mei');
  assert.deepEqual(drafts.read(), { owner: 'mei', body: '上次离线填写的送货地址', receipt: null });
});

test('当前账号的提交发送正文并持久化返回的回执', async () => {
  const records = new Map();
  const drafts = openDrafts('lin', records, async (owner, body) => {
    assert.equal(owner, 'lin');
    assert.equal(body, '送到前台');
    return 'R7';
  });
  drafts.edit({ body: '送到前台' });
  assert.equal(await drafts.submit(), 'saved');
  const expected = { owner: 'lin', body: '送到前台', receipt: 'R7' };
  assert.deepEqual(drafts.read(), expected);
  assert.deepEqual(openDrafts('lin', records, async () => 'R8').read(), expected);
});

for (const active of ['mei', 'lin']) {
  test(`发送后切换到 mei，回执抵达时当前账号为 ${active}`, async () => {
    const records = new Map([['mei', JSON.stringify({ version: 2, body: '西门', receipt: 'R2' })]]);
    const sent = Promise.withResolvers();
    const reply = Promise.withResolvers();
    const drafts = openDrafts('lin', records, (owner, body) => {
      sent.resolve({ owner, body });
      return reply.promise;
    });

    drafts.edit({ body: '东门' });
    const pending = drafts.submit();
    assert.deepEqual(await sent.promise, { owner: 'lin', body: '东门' });
    drafts.select('mei');
    if (active === 'lin') drafts.select('lin');
    reply.resolve('LATE');
    const outcome = await pending;

    const expected = {
      mei: { owner: 'mei', body: '西门', receipt: 'R2' },
      lin: { owner: 'lin', body: '东门', receipt: null },
    };
    assert.deepEqual(drafts.read(), expected[active]);
    for (const [owner, draft] of Object.entries(expected)) {
      assert.deepEqual(openDrafts(owner, records, async () => 'R3').read(), draft);
    }
    assert.equal(outcome, 'superseded');
  });
}
