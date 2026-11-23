<!--
目标路径:.github/PULL_REQUEST_TEMPLATE.md
由 uni-github-delivery-setup/templates/ 同步而来 —— 基础版,各仓可在「验证 / 影响范围」补 repo 特有项。
-->
## 变更概述

<!-- 1-2 句:做了什么 / 为什么。链接 issue 用 `Closes #N`。 -->

## 类型

<!-- conventional-commits 类型,跟 commit msg 对齐。多选用 - [x] -->

是否发版按工作流触发范围和版本规则判断。

- [ ] `feat` 新功能（通常对应 minor）
- [ ] `fix` Bug 修复（通常对应 patch）
- [ ] `refactor` / `chore` / `docs` / `test` / `ci`
- [ ] **包含 BREAKING CHANGE**（可能触发 major，须先取得明确授权，在 commit body 写 `BREAKING CHANGE: ...`）

## 验证

- [ ] `yarn lint`
- [ ] `yarn typecheck`
- [ ] `yarn test`
- [ ] (若改了原生 / RN 代码)在 `example/` 里跑过

## 影响范围 / 注意点

<!-- 哪些模块受影响 / 消费者是否需要同步改动 / 是否有 BREAKING CHANGE -->
