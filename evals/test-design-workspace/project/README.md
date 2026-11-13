# 送货草稿编辑器

客户切换账号时会在同一编辑器打开另一个账号的草稿。部署包只向编辑器提供 `src/drafts.mts` 的 `openDrafts(owner, records, send)`。可用 Node.js 22.18 或更高版本在此目录离线执行 `node --test test/*.test.mts`。

- `records` 是按账号索引、值为 JSON 字符串的本地草稿库。`samples/upgrade-v1.json` 来自仍受支持的上一版安装，用户可以跳过中间版本直接升级。该版用 `text` 保存正文，没有回执。现版用 `{version: 2, body, receipt}` 保存，无回执时为 `null`。
- `select(owner)` 切换当前账号并读取其草稿。`read()` 返回当前 `{owner, body, receipt}`，新草稿正文为空，无回执。
- 编辑器通过 `edit({body})` 保存本地正文并清空回执。正文必须是字符串，缺少或类型错误时抛出 `TypeError`，原草稿仍可读。提交之前使用的内部编辑对象只在进程内生成，未进入草稿库或重放队列。编辑器是该实现唯一的调用方，没有扩展入口。
- `submit()` 调用 `send(owner, body)`。当前账号收到成功回执时保存回执并返回 `'saved'`。若等待期间切到了另一个账号，旧操作返回 `'superseded'`，两个账号的草稿均保留原有内容和回执。
