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

## 使用

可以加载完整插件，也可以只提供所需的 `skills/<技能名>/` 目录。单独使用时保留该目录中的 `SKILL.md`、`references/` 和 `agents/`，通过所用工具的技能安装机制启用。

每个技能的必要资料都在自身目录内，不需要复制仓库根目录或安装其他技能。技能之间的组合入口只在任务需要且对应技能可用时采用。描述用于自动识别任务，也可显式指定完整技能名称。

插件定义见 [plugin.json](plugin.json)，市场入口见 [marketplace.json](.agents/plugins/marketplace.json)。仓库源码、插件分发及工具实际加载分别核对，不以文件存在代表已安装或已发布。

## 维护

修改所属技能及其引用资料，保持触发范围明确。通用规则不绑定某个企业、应用、固定包名或个人路径；项目已有有效约定与工具要求优先。

使用[评测任务](evals/cases.md)检查实际输出、独立使用和任务边界，再核对格式、相对引用及插件清单。行为运行记录放在仓库外；计划和设计保留在 `docs/`，不进入技能默认上下文。
