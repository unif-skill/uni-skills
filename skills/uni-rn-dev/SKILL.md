---
name: uni-rn-dev
description: 在 React Native 应用或库中实现、调整或审查组件、Hook、样式、交互状态、平台适配、原生接入和工程检查配置，或进行 iOS 真机安装、Metro 调试及设备连接恢复时使用。不用于纯文案修改或原生鸿蒙代码。
---

# React Native 开发规范

按当前 React/RN 版本、项目契约和实际平台实现功能，保持组件状态、调用与资源的正确归属。

## 按任务读取

| 当前工作 | 资料 |
|---|---|
| 新工程、默认开发规范、ESLint／TypeScript／格式或提交检查接入，以及变更前核对现有门禁 | [默认开发检查](references/quality.md)及其配置模板 |
| 组件、Hook、受控交互、主题和样式 | [组件与状态](references/components.md) |
| 平台适配、原生依赖、宿主与验证 | [平台接入](references/platform-integration.md) |
| iOS 实体设备安装、当前 JS 核实、Metro 或自动化连接恢复 | [iOS 安装与调试](references/ios-device-debugging.md) |

目录、文件和工程命令从项目维护入口及配置取得。按任务选用 `uni-code-organization`、`uni-rn-library` 或 `uni-documentation`，无需作为前置加载。

RN 默认采用 ESLint、Prettier、严格 TypeScript 与 Husky／lint-staged／commitlint。新增或升级工程检查按默认开发检查落实；日常开发读取项目已采用配置，在本次范围内通过检查并保留有效例外，不因加载技能自动迁移整个工程。

## 实施

接续任务先核对最新已确认范围、排除项和已撤回方案，再沿真实页面或调用入口检查现有组件、SDK、状态归属与消费者。组件、应用组合与原生能力保留各自职责，按实际缺口决定复用、扩展或替换。

涉及第三方库、框架或 SDK 时，先按实际采用版本核对官方推荐用法与限制；排障同时确认修复是否已发布及适用，再决定配置、升级或自有修复。详细核查可选用 `uni-third-party-integration`。不能把架构候选当成已发布 API，也不因“更新”改变依赖、默认行为或支持范围。平台和设备差异保持明确。

UI、默认值、事件、错误、取消、权限和资源语义随有效契约保持。替换后迁移相关消费者，清理确认失效的实现、导出和接线。修改后检查组件、实际使用场景与必要宿主；类型、自动化、构建、页面或设备与业务验收分别报告。
