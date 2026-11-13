import { editBody } from './edit.mts';

type Draft = { owner: string; body: string; receipt: string | null };
type Send = (owner: string, body: string) => Promise<string>;

function restore(owner: string, raw: string | undefined): Draft {
  if (raw === undefined) return { owner, body: '', receipt: null };
  const record = JSON.parse(raw);
  if (record.version === 1) return { owner, body: record.text, receipt: null };
  return { owner, body: record.body, receipt: record.receipt };
}

export function openDrafts(owner: string, records: Map<string, string>, send: Send) {
  let current = restore(owner, records.get(owner));

  function persist() {
    const { owner, body, receipt } = current;
    records.set(owner, JSON.stringify({ version: 2, body, receipt }));
  }

  return {
    select(owner: string) {
      current = restore(owner, records.get(owner));
    },
    read() {
      return { ...current };
    },
    edit(input: unknown) {
      if (!input || typeof input !== 'object' || !('body' in input) || typeof input.body !== 'string') {
        throw new TypeError('需要正文');
      }
      current.body = editBody({ body: input.body });
      current.receipt = null;
      persist();
    },
    async submit() {
      const receipt = await send(current.owner, current.body);
      current.receipt = receipt;
      persist();
      return 'saved';
    },
  };
}
