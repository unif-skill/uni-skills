---
name: uni-harmony-dev
description: 在原生 HarmonyOS 应用或库中实现、调整、排查或审查 ArkTS／ArkUI 组件、状态、生命周期、平台适配及 SDK 接入时使用。不用于 RN／RNOH 实现或纯文档修改。
---

# HarmonyOS 开发规范

以 HarmonyOS API 26 和 ArkUI V2 为开发基线，按有效契约实现功能。应用、库与平台宿主分别承担自己的状态和资源责任。

## 按任务读取

| 当前工作 | 资料 |
|---|---|
| ArkUI 输入、状态、组件和页面生命周期、主题与布局 | [组件与状态](references/components-state.md) |
| Context、原生能力、权限、异步操作、文件及验证 | [平台接入](references/platform-integration.md) |

本目录包含所需开发指引，可独立使用。目录与文件按工程有效约定组织；其他已安装技能仅按实际任务选用，不是安装或调用前置。

## 实施

先核对工程的 target／compatible SDK、实际编译器与工具版本是否满足 API 26 目标，再检查已有组件及公开能力。语言语法、装饰器、API 签名、权限和错误语义从 API 26 SDK 的类型、官方资料与项目代码取得；资料快照或同名 API 不证明当前版本支持。

新 UI 使用 API 26 支持的 V2 状态能力，开发与验证不扩展旧 API 或 V1 兼容。目标环境不满足基线时说明差异，不自行降低标准或扩大工程升级范围。原生工程不照搬 TSX、Hooks、RN 样式、Metro 或 Pods；普通 TS 是否可用按真实依赖和目标互操作能力验证。

局部修改保留已确认的输入输出、视觉、交互、取消和业务成功条件。开发前确认实际消费者，完成后分别报告静态检查、自动化、构建、宿主运行及未验证的设备或业务行为；只读 API 查询不要求执行完整开发流程。

函数职责与异步流程重构可选用 `uni-code-organization`，源码契约注释可选用 `uni-documentation`；这些通用规则不替代 ArkTS／ArkUI 的语言限制、平台生命周期和实际调用验证。
