# Uni Skills

通用工程技能集合，提供第三方技术接入、代码组织、React Native 与 HarmonyOS 开发、库工程、文档规范、技能编写和 GitHub 交付工具。

## 技能

| 技能 | 用途 |
|---|---|
| [uni-third-party-integration](skills/uni-third-party-integration/SKILL.md) | 第三方库、框架与 SDK 的设计、接入、封装、升级评估及排障 |
| [uni-code-organization](skills/uni-code-organization/SKILL.md) | 跨语言代码开发、维护和审查中的职责、条件、类型、依赖、异步、注释及工程配置 |
| [uni-rn-dev](skills/uni-rn-dev/SKILL.md) | RN 组件、Hook、样式、平台接入与 iOS 安装调试 |
| [uni-rn-library](skills/uni-rn-library/SKILL.md) | RN 库创建、提取、维护、打包、发布与运行示例 |
| [uni-harmony-dev](skills/uni-harmony-dev/SKILL.md) | API 26／V2 下的 ArkTS／ArkUI 状态、宿主生命周期、平台接入与资源交接 |
| [uni-harmony-library](skills/uni-harmony-library/SKILL.md) | API 26 原生 HAR 库公共入口、依赖资源、打包发布与真实宿主示例 |
| [uni-github-delivery](skills/uni-github-delivery/SKILL.md) | GitHub CI、仓库保护、工程模板同步、发布与恢复检查 |
| [uni-documentation](skills/uni-documentation/SKILL.md) | 各类工程的文档编写、组织与审校，以及文档站生成、构建和验证 |
| [uni-skill-authoring](skills/uni-skill-authoring/SKILL.md) | 技能内容编写与审校、适用范围、触发描述和配套资料维护 |

技能按实际任务独立发现和使用，不要求相互安装或调用。GitHub 交付的共用机制在 uni-github-delivery 维护；组织约定由所属组织提供，接入时落实到目标工程配置，通用工具不查找其他技能的安装目录。

这些规范适用于不同企业和项目。具体技术选型、业务目录、CI、发布方式和能力契约从目标项目取得；文档规范适用于 RN、鸿蒙、脚本及其他技术工程。

## 安装

Codex 可通过插件入口安装本仓的 Uni Skills 插件，技能在同一插件下展示。需要其他本地工具共用时，另用下面的方式保留共享技能目录。

使用 [Vercel Skills](https://github.com/vercel-labs/skills) 为所选的本地编程工具安装技能。需要 Node.js 22.20+；访问私有仓库时，先配置有权读取仓库的 Git 或 GitHub CLI 登录。

```sh
npx skills add unif-skill/uni-skills -g \
  --agent codex claude-code cursor --skill '*'
```

`-g` 表示在本机跨项目使用；按需调整 `--agent` 后的工具名单。只安装某个技能时，将 `--skill '*'` 改成例如 `--skill uni-documentation`。

默认采用共享副本与软链接：

| 工具 | 本机技能入口 |
|---|---|
| Codex、Cursor | 直接读取 `~/.agents/skills/<技能名>/` |
| Claude Code | `~/.claude/skills/<技能名>/` 链接到共享副本 |

同一工具只启用一种加载入口。Codex 使用插件时，在其技能设置中禁用对应的共享技能入口；共享目录仍可保留给 Claude Code、Cursor 等工具。安装后核对实际发现和启用状态，避免重复加载。上述入口用于本地工具；网页和云端会话按对应产品的安装机制配置。

## 使用与更新

按任务自动选择技能，也可显式指定技能名称。每个技能的必要资料都在自己的目录内，支持独立使用；组合入口只在任务需要且其他技能可用时采用。

更新本集合的技能：

```sh
npx skills update -g uni-code-organization uni-rn-dev \
  uni-rn-library uni-harmony-dev uni-harmony-library \
  uni-documentation uni-skill-authoring uni-github-delivery uni-third-party-integration
```

此命令更新已安装的共享副本；首次添加新技能时重新执行上方安装命令。Codex 插件按插件机制单独更新，不会自动改写共享目录。两种入口并存时分别更新并核对同一版本的内容，继续禁用 Codex 的重复共享入口。安装或更新后，在目标工具中确认技能可见；旧会话仍使用缓存时，重新打开会话。

## 维护

修改所属技能及其引用资料，保持触发范围明确。通用规则不绑定某个企业、应用、固定包名或个人路径；项目已有有效约定与工具要求优先。

技能正文保留任务判断、操作、必要来源和验证；技能仓的维护分工、生成和分发流程放在本 README 或对应维护入口。讨论过程不直接写入技能，只保留必要且可复用的结论。涉及操作的版本、授权、平台和资源限制仍在对应步骤说明。

维护脚本回归使用 `python3 -m unittest discover -s tests -v`，配置测试只使用合成配置，不读取真实凭据。`python -m scripts.validate_repository` 另核对插件清单、版本、仓内入口和已采用发布工具；交付工具的完整检查继续运行 `bash skills/uni-github-delivery/scripts/validate.sh`。

RN 默认开发检查及配置模板以 `uni-rn-dev/references/quality.md` 和 `uni-rn-dev/templates/quality/` 为维护源；修改后运行 `python scripts/sync_rn_quality.py`，同步到 RN 库和 GitHub 交付技能的独立副本，再用 `--check` 核对。消费者无需安装其他技能，也不读取技能仓根目录脚本。质量模板按目标工程合并采用，不覆盖已有工具链、规则和有效例外，不自动迁移其他仓库。

模板的真实工具回归使用 `npm ci --prefix tests/fixtures/rn-quality --ignore-scripts --no-audit --no-fund` 安装锁定的隔离工具，再运行 `node --test tests/rn-quality.test.cjs`。覆盖规则正反例、库声明输出、格式及实际提交钩子的拦截、放行和部分暂存保护；这些结果不替代 RN 应用构建或设备验收。

使用[评测任务](evals/cases.md)检查实际输出、独立使用和任务边界，再核对格式、相对引用及插件清单。行为运行记录放在仓库外；计划和设计保留在 `docs/`，不进入技能默认上下文。

[RN 平台独立使用](evals/rn-platform-ownership.md)覆盖 iOS 安装调试和变更验证范围，核对通用流程不依赖企业技能。

### 查看评测报告

[工程校验](https://github.com/unif-skill/uni-skills/actions/workflows/validate.yml)与[模型行为评测](https://github.com/unif-skill/uni-skills/actions/workflows/behavior-eval.yml)分别记录结果。在模型评测的运行页查看 **Summary** 下方的结论、完成配对和请求次数；完整报告与读取轨迹从 **Artifacts** 下载。

工作流允许模型评测失败，绿色状态不代表技能效果通过。选题范围、模型配置、判分与本地运行方法见[行为评测说明](evals/behavior/README.md)。

### 自动发版与共享工具

main 推送通过现有完整 CI 验证后，发布步骤核对候选版本并创建对应 GitHub Release。需要递增版本时，仅将新版本写回 `plugin.json`，重新验证后提交；仅发布 job 使用仓库自带 `GITHUB_TOKEN` 的内容写权限。PR、tag 和手动工作流只验证，不发布。版本写回使用 `GITHUB_TOKEN` 并带 `[skip ci]` 标记，避免自触发。

minor 与 patch 按提交类型选择：检查当前版本标签到本次已验证提交之间的标题，包含 `feat: ...`、`feat(scope): ...` 等 feat 类型时递增 minor 并将 patch 归零，其余递增 patch。提交正文中的 feat 不参与判断，`!` 标记不触发 major 升级。清单明确指定同一 major 内尚未发布的新 minor／patch 时保留该版本；跨 major 变化会停止，须单独确认后再按获准流程处理。重复运行只恢复同一已知发布提交，不覆盖其他提交的标签，也不以再次发版掩盖验收失败。

两个发布脚本和两份行为测试由 `unif-skill/unif-portal-dev-skills` 单一维护，本仓保留同源副本和逐文件摘要。升级时从显式指定的本地源码同步，在 Uni 仓执行：

```sh
python -m scripts.sync_release_tools --source /path/to/unif-portal-dev-skills --check
python -m scripts.sync_release_tools --source /path/to/unif-portal-dev-skills
```

`--check` 只读比较指定来源；不带该参数时仅更新四个受管文件及 `scripts/release-tools.json`，保留其他项目文件，不提交或修改远端。发现本地受管文件与已采用摘要不一致时停止，先核对差异归属。来源仓不是 CI 或插件运行依赖，不需要增加访问其他私有仓的凭证；摘要校验表示已采用内容一致，不代表采用了上游最新版本。审查同步差异并通过测试后，按本次授权正常提交。
