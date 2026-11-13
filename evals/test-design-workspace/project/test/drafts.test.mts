import assert from 'node:assert/strict';
import test from 'node:test';
import { openDrafts } from '../src/drafts.mts';
import { editBody, type DraftEdit } from '../src/edit.mts';

test('编辑器通过公开入口替换当前草稿正文', () => {
  const drafts = openDrafts('lin', new Map(), async () => 'R1');
  drafts.edit({ body: '周一交货' });
  assert.equal(drafts.read().body, '周一交货');
});

test('旧编辑对象可以通过 replacement 替换正文', () => {
  const input = { replacement: '明早交货' } as unknown as DraftEdit;
  assert.equal(editBody(input), '明早交货');
});
