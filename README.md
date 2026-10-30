# Uni Skills

通用工程技能集合，提供代码组织、React Native 开发、库工程和文档规范。每个技能独立维护，也可以按任务组合使用。

## 技能

| 技能 | 用途 |
|---|---|
| [code-organization](skills/code-organization/SKILL.md) | 前端、RN、鸿蒙等工程的目录归属、文件角色、命名与公共入口 |
| [react-native-development](skills/react-native-development/SKILL.md) | RN 组件、Hook、样式、交互状态与原生平台接入 |
| [react-native-library](skills/react-native-library/SKILL.md) | RN 库创建、提取、维护、打包、发布与运行示例 |
| [documentation](skills/documentation/SKILL.md) | 各类工程的文档编写、组织与审校，以及文档站生成、构建和验证 |

这些规范适用于不同企业和项目。具体技术选型、业务目录、CI、发布方式和能力契约从目标项目取得；文档规范适用于 RN、鸿蒙、脚本及其他技术工程。

## 安装

使用 [Vercel Skills](https://github.com/vercel-labs/skills) 为所选的本地编程工具安装技能。需要 Node.js 22.20+；访问私有仓库时，先配置有权读取仓库的 Git 或 GitHub CLI 登录。

```sh
npx skills add unif-skill/uni-skills -g \
  --agent codex claude-code cursor --skill '*'
```

`-g` 表示在本机跨项目使用；按需调整 `--agent` 后的工具名单。只安装某个技能时，将 `--skill '*'` 改成例如 `--skill documentation`。

默认采用共享副本与软链接：

| 工具 | 本机技能入口 |
|---|---|
| Codex、Cursor | 直接读取 `~/.agents/skills/<技能名>/` |
| Claude Code | `~/.claude/skills/<技能名>/` 链接到共享副本 |

同一工具选择一种安装方式。已有插件版时，先确认新入口可发现，再移除重复插件。上述入口用于本地工具；网页和云端会话按对应产品的安装机制配置。

## 使用与更新

按任务自动选择技能，也可显式指定技能名称。每个技能的必要资料都在自己的目录内，支持独立使用；组合入口只在任务需要且其他技能可用时采用。

更新本集合的四个技能：

```sh
npx skills update -g code-organization react-native-development \
  react-native-library documentation
```

更新会刷新安装的共享副本，各工具通过原入口读取。安装或更新后，在目标工具中确认技能可见；旧会话仍使用缓存时，重新打开会话。

## 维护

修改所属技能及其引用资料，保持触发范围明确。通用规则不绑定某个企业、应用、固定包名或个人路径；项目已有有效约定与工具要求优先。

使用[评测任务](evals/cases.md)检查实际输出、独立使用和任务边界，再核对格式、相对引用及插件清单。行为运行记录放在仓库外；计划和设计保留在 `docs/`，不进入技能默认上下文。
