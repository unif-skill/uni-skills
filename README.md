# Uni Skills

通用工程技能集合，提供代码组织、React Native 与 HarmonyOS 开发、库工程、文档规范和 GitHub 交付工具。每个技能独立维护，也可以按任务组合使用。

## 技能

| 技能 | 用途 |
|---|---|
| [uni-code-organization](skills/uni-code-organization/SKILL.md) | 前端、RN、鸿蒙、后端等工程的目录归属、源码与配置文件、环境变体、命名与公共入口 |
| [uni-rn-dev](skills/uni-rn-dev/SKILL.md) | RN 组件、Hook、样式、平台接入与 iOS 安装调试 |
| [uni-rn-library](skills/uni-rn-library/SKILL.md) | RN 库创建、提取、维护、打包、发布与运行示例 |
| [uni-harmony-dev](skills/uni-harmony-dev/SKILL.md) | API 26／V2 下的 ArkTS／ArkUI 状态、宿主生命周期、平台接入与资源交接 |
| [uni-harmony-library](skills/uni-harmony-library/SKILL.md) | API 26 原生 HAR 库公共入口、依赖资源、打包发布与真实宿主示例 |
| [uni-github-delivery](skills/uni-github-delivery/SKILL.md) | GitHub CI、仓库保护、工程模板同步、发布与恢复检查 |
| [uni-documentation](skills/uni-documentation/SKILL.md) | 各类工程的文档编写、组织与审校，以及文档站生成、构建和验证 |

技能按实际任务独立发现和使用，不要求相互安装或调用。GitHub 交付的共用机制在 uni-github-delivery 维护；组织约定由所属组织提供，接入时落实到目标工程配置，通用工具不查找其他技能的安装目录。

这些规范适用于不同企业和项目。具体技术选型、业务目录、CI、发布方式和能力契约从目标项目取得；文档规范适用于 RN、鸿蒙、脚本及其他技术工程。

## 0.4.0 名称迁移

全部技能以 `uni-` 开头；平台段使用 `rn` 和 `harmony`。

| 原名称 | 当前名称 |
|---|---|
| `code-organization` | `uni-code-organization` |
| `documentation` | `uni-documentation` |
| `github-delivery` | `uni-github-delivery` |
| `react-native-development` | `uni-rn-dev` |
| `react-native-library` | `uni-rn-library` |
| `harmonyos-development` | `uni-harmony-dev` |
| `harmonyos-library` | `uni-harmony-library` |

名称变化需要重新安装对应的新技能，不能只用旧名执行 update。先安装并核对新目录，再按同一安装范围移除旧入口；Codex 插件随新版本替换入口，共享副本单独迁移并保留既有启用策略。历史设计与计划保留当时名称，当前调用以上表为准。

交付采用记录的 `standard` 改为 `uni-github-delivery/rn`。已有工程使用新技能的同步命令更新受管脚本和 `.github/delivery.json`，再运行仓内检查；不要只替换标准字符串或手写摘要。采用记录和工程配置按该工程的交付范围提交。

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
  uni-documentation uni-github-delivery
```

此命令更新已安装的共享副本；首次添加新技能时重新执行上方安装命令。Codex 插件按插件机制单独更新，不会自动改写共享目录。两种入口并存时分别更新并核对同一版本的内容，继续禁用 Codex 的重复共享入口。安装或更新后，在目标工具中确认技能可见；旧会话仍使用缓存时，重新打开会话。

## 维护

修改所属技能及其引用资料，保持触发范围明确。通用规则不绑定某个企业、应用、固定包名或个人路径；项目已有有效约定与工具要求优先。

维护脚本回归使用 `python3 -m unittest discover -s tests -v`，配置测试只使用合成配置，不读取真实凭据。`python -m scripts.validate_repository` 另核对插件清单、版本、仓内入口和已采用发布工具；交付工具的完整检查继续运行 `bash skills/uni-github-delivery/scripts/validate.sh`。

使用[评测任务](evals/cases.md)检查实际输出、独立使用和任务边界，再核对格式、相对引用及插件清单。行为运行记录放在仓库外；计划和设计保留在 `docs/`，不进入技能默认上下文。

[RN 平台独立使用](evals/rn-platform-ownership.md)覆盖 iOS 安装调试和变更验证范围，核对通用流程不依赖企业技能。

### 行为评测 CI

独立的[行为评测工作流](.github/workflows/behavior-eval.yml)在 PR、main 的技能、题库、分发入口或评测工具变化时运行。默认 `scope=affected` 按变更技能、插件及实际发现关联选题；技能源与生成副本去重，纯版本和溯源记录变化不触发模型评测。共享评测机制变化或显式 `scope=all` 才覆盖全库，详细规则见[选题范围](evals/behavior/README.md#本次选题范围)。

`mode` 只决定重复次数：`smoke` 为每题旧版、候选各 1 次，`full` 为各 10 次，不再决定选题范围。PR 的 `auto` 使用 `smoke`；main 推送及手动 `auto` 遇到比较范围中的 `feat` 提交或根清单 major／minor 提升时使用 `full`，其余使用 `smoke`。无受影响题目时直接跳过，不因版本提升制造评测任务。10 对是当前统计比较协议，不能与历史 5 次重复或其他模型样本混合。

手动运行可分别选择 `scope`、`mode` 和基线 `base_ref`。PR 使用目标分支的 `base.sha`，main 推送使用 `before`，手动未填基线时使用 `HEAD^`；历史缺失或基线不可解析会报告证据不足，不回退到候选自比。

工作流先离线核对题库与受管文件，再在同一次运行中使用同一题库、模型和判据比较固定基线与候选。模型只读固定题设和允许的技能资料，不执行 shell、写文件或调用业务系统。机器题库及覆盖范围见[行为评测说明](evals/behavior/README.md)；现有题库、人工判据和本地专项回归继续保留，首版 CI 只执行自包含题，不代表已迁移全部历史案例。应用题由独立模型调用按冻结判据评阅，保留理由并需人工抽查。

通过百炼调用 DeepSeek 时，在仓库 Actions 配置以下变量和密钥；工作流不会自动配置密钥或开启模型调用。有待评测题目而缺配置、外部 fork PR 无密钥、预算耗尽或运行不完整时生成“证据不足”摘要；无相关变化时明确标记跳过。

| 配置 | 类型 | 用途 |
|---|---|---|
| `SKILL_EVAL_ENABLED` | variable | 设为 `true` 才启用模型调用 |
| `SKILL_EVAL_MODEL` | variable | 百炼答题模型标识，例如 `deepseek-v4-pro` |
| `SKILL_EVAL_JUDGE_MODEL` | variable，可选 | 评阅模型；未填时用答题模型的独立上下文 |
| `SKILL_EVAL_MAX_REQUESTS` | variable | 单次运行的总 API 请求次数上限，包含答题与评阅；不是美元预算 |
| `UNIF_MODEL_BASE_URL` | variable | 百炼兼容接口地址：`https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `UNIF_MODEL_API_KEY` | secret | 百炼 API Key；无需 OpenAI 或 DeepSeek 官网 Key，不使用本机 OAuth 或用户订阅鉴权 |

模型示例的账号权限、服务可用性与兼容返回需在首次真实调用时核验；写入配置不代表已经验证。

摘要展示改善、退化、持平（本样本未观察到差异）或证据不足；退出码 `0` 表示完成或无相关变化，`1` 表示有证据支持退化，`2` 表示证据不足。GitHub step summary 展示结论和原始退出码，artifact 保留 `summary.md`、`summary.json`、记录步骤结果与退出码的 `workflow.json`、逐题失败例、原始回答与读取轨迹 30 天。请求次数限制、180 分钟超时及同 ref 取消旧运行控制执行规模；它们不承诺实际费用。此工作流不写 PR 评论，仅供查看：job 和模型运行步骤允许失败，不纳入分支必需检查，也不成为现有校验或发布的依赖。密钥缺失、退化、证据不足及评测基础设施错误均不阻断原有发布流程；发布继续依据原有校验。报告保留真实四态与退出码，成功生成报告不等于模型通过。

本地可先离线验证与规划；将 `BASE_SHA`、`HEAD_SHA` 设为实际比较修订。最后一条命令仅在显式启用并提供上述配置时调用模型，输出放在仓库外：

```sh
python scripts/sync_evaluation_tools.py --verify
python scripts/behavior_eval.py validate --root .
python scripts/behavior_eval.py plan --repo . --base "$BASE_SHA" --head "$HEAD_SHA" --scope affected --mode smoke --event workflow_dispatch --output /tmp/skill-eval-plan.json
python scripts/behavior_eval.py run --plan /tmp/skill-eval-plan.json --output-dir /tmp/skill-eval-artifacts
```

通用评测器、测试与工作流由 Uni 维护，Unif 通过 `scripts/sync_evaluation_tools.py` 显式采用同源副本；各仓 CI 只运行仓内文件，不访问其他私有仓。离线校验、模型样本结果、实际宿主加载、设备及业务验收分别提供证据，CI 结果不能保证模型对其他任务正确。

### 自动发版与共享工具

main 推送通过现有完整 CI 验证后，发布步骤核对候选版本并创建对应 GitHub Release。需要递增版本时，仅将新版本写回 `plugin.json`，重新验证后提交；仅发布 job 使用仓库自带 `GITHUB_TOKEN` 的内容写权限。PR、tag 和手动工作流只验证，不发布。版本写回使用 `GITHUB_TOKEN` 并带 `[skip ci]` 标记，避免自触发。

minor 与 patch 按提交类型选择：检查当前版本标签到本次已验证提交之间的标题，包含 `feat: ...`、`feat(scope): ...` 等 feat 类型时递增 minor 并将 patch 归零，其余递增 patch。提交正文中的 feat 不参与判断，`!` 标记不触发 major 升级。清单明确指定同一 major 内尚未发布的新 minor／patch 时保留该版本；跨 major 变化会停止，须单独确认后再按获准流程处理。重复运行只恢复同一已知发布提交，不覆盖其他提交的标签，也不以再次发版掩盖验收失败。

两个发布脚本和两份行为测试由 `unif-skill/unif-portal-dev-skills` 单一维护，本仓保留同源副本和逐文件摘要。升级时从显式指定的本地源码同步，在 Uni 仓执行：

```sh
python -m scripts.sync_release_tools --source /path/to/unif-portal-dev-skills --check
python -m scripts.sync_release_tools --source /path/to/unif-portal-dev-skills
```

`--check` 只读比较指定来源；不带该参数时仅更新四个受管文件及 `scripts/release-tools.json`，保留其他项目文件，不提交或修改远端。发现本地受管文件与已采用摘要不一致时停止，先核对差异归属。来源仓不是 CI 或插件运行依赖，不需要增加访问其他私有仓的凭证；摘要校验表示已采用内容一致，不代表采用了上游最新版本。审查同步差异并通过测试后，按本次授权正常提交。
