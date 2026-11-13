export type DraftEdit = { body: string };

export function editBody(edit: DraftEdit): string {
  if ('replacement' in edit && typeof edit.replacement === 'string') {
    return edit.replacement;
  }
  return edit.body;
}
