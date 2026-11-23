# Uni Skills

13 项可独立安装的通用工程技能，覆盖代码变更、故障诊断、代码审查、测试与验证，以及平台开发、依赖接入、文档、技能编写和 GitHub 交付配置。

## 技能

| 技能 | 用途 |
|---|---|
| [uni-third-party-integration](skills/uni-third-party-integration/SKILL.md) | 第三方库、框架与 SDK 的设计、接入、封装、升级评估及排障 |
| [uni-code-change](skills/uni-code-change/SKILL.md) | 实现明确需求，重构代码、调整工程配置或清理已确认的废弃路径 |
| [uni-debugging](skills/uni-debugging/SKILL.md) | 从实际失败入口复现故障，定位根因并验证获准的修复 |
| [uni-code-review](skills/uni-code-review/SKILL.md) | 审查 PR、提交或工作区差异，给出可定位的触发条件、后果和依据 |
| [uni-verify-change](skills/uni-verify-change/SKILL.md) | 按实际差异和消费者选择并运行检查，说明结果及未覆盖范围 |
| [uni-test-design](skills/uni-test-design/SKILL.md) | 新功能的行为测试、已有系统的回归与覆盖率门禁 |
| [uni-rn-dev](skills/uni-rn-dev/SKILL.md) | RN 组件、Hook、样式、平台接入与 iOS 安装调试 |
| [uni-rn-library](skills/uni-rn-library/SKILL.md) | RN 库创建、提取、维护、打包、发布与运行示例 |
| [uni-harmony-dev](skills/uni-harmony-dev/SKILL.md) | API 26／V2 下的 ArkTS／ArkUI 状态、宿主生命周期、平台接入与资源交接 |
| [uni-harmony-library](skills/uni-harmony-library/SKILL.md) | API 26 原生 HAR 库公共入口、依赖资源、打包发布与真实宿主示例 |
| [uni-github-delivery-setup](skills/uni-github-delivery-setup/SKILL.md) | 建设或核查 GitHub CI、规则集、仓库保护、模板同步及发布恢复配置 |
| [uni-documentation](skills/uni-documentation/SKILL.md) | 各类工程的文档编写、组织与审校，以及文档站生成、构建和验证 |
| [uni-skill-authoring](skills/uni-skill-authoring/SKILL.md) | 技能内容编写与审校、适用范围、触发描述和配套资料维护 |

技能按实际任务独立发现和使用，不要求相互安装或调用。GitHub 交付的共用机制在 uni-github-delivery-setup 维护；组织约定由所属组织提供，接入时落实到目标工程配置，通用工具不查找其他技能的安装目录。

这些规范适用于不同企业和项目。具体技术选型、业务目录、CI、发布方式和能力契约从目标项目取得；文档规范适用于 RN、鸿蒙、脚本及其他技术工程。

RN 与鸿蒙规则分为平台通用方法和项目采用两层：`uni-rn-dev`、`uni-harmony-dev` 维护组件、状态、生命周期和平台接入方法，`uni-rn-library`、`uni-harmony-library` 维护库工程、分发产物与独立消费者验证。项目专项技能维护目录、选型、业务契约和验收对象，按需要引用通用技能，不复制通用正文。通用技能无需项目专项技能即可使用。

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
npx skills update -g uni-code-change uni-debugging uni-code-review \
  uni-verify-change uni-test-design uni-rn-dev \
  uni-rn-library uni-harmony-dev uni-harmony-library \
  uni-documentation uni-skill-authoring uni-github-delivery-setup uni-third-party-integration
```

此命令更新已安装的共享技能。使用早期版本共享入口的工程按以下顺序处理。

1. 按原安装范围与工具执行上方 `skills add`，安装本次需要的新入口。在实际使用的工具中核对所选技能可见。
2. 查安装记录，确认以下旧入口来自本集合，然后按原范围与工具移除。下例对应全局安装到 Codex、Claude Code 和 Cursor。项目级安装在对应工程内执行，省略 `-g`，并按原安装情况调整 `--agent` 名单。

   ```sh
   npx skills remove uni-code-organization uni-github-delivery -g --agent codex claude-code cursor
   ```

3. 在目标工具核对最终可用的入口，旧会话仍使用缓存时重新打开。命令只指定这两个已经确认来源的名称。若同名技能来自其他来源，保留其安装。[Vercel Skills 移除命令](https://github.com/vercel-labs/skills/blob/main/src/remove.ts)

整插件安装通过 Codex 插件入口更新。共享安装和插件并存时分别更新，继续禁用 Codex 的重复共享入口。

## 维护

修改所属技能及其引用资料，保持触发范围明确。通用规则不绑定某个企业、应用、固定包名或个人路径；项目已有有效约定与工具要求优先。

技能正文保留任务判断、操作、必要来源和验证；技能仓的维护分工、生成和分发流程放在本 README 或对应维护入口。讨论过程不直接写入技能，只保留必要且可复用的结论。涉及操作的版本、授权、平台和资源限制仍在对应步骤说明。

维护、校验和评测使用 Python 3.12；读取技能正文不要求该运行环境。创建独立环境并安装固定的校验依赖：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements-ci.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m scripts.validate_repository
```

上述命令显式使用工程环境，不依赖系统 `python3` 指向的版本。配置测试使用合成配置，不读取真实凭据。仓库校验覆盖插件清单、版本、技能格式、YAML、本地链接与锚点、已声明资产和已采用发布工具；图标与配套资料目录按技能需要配置。交付工具的完整检查继续运行 `bash skills/uni-github-delivery-setup/scripts/validate.sh`。

通用技能文件校验在 `scripts/skill_validation.py` 维护。Unif 通过显式同步采用模块、测试、依赖清单和类型声明；运行时只使用仓内副本，组织与生成资料检查仍由 Unif 自身维护：

```sh
.venv/bin/python scripts/sync_validation_tools.py \
  --source . --target /path/to/unif-portal-dev-skills
.venv/bin/python scripts/sync_validation_tools.py \
  --source . --target /path/to/unif-portal-dev-skills --check
```

`--check` 只读比较指定来源。采用仓运行 `python scripts/sync_validation_tools.py --verify` 核对副本与已登记摘要，不访问维护源；同步拒绝覆盖无法核实归属的已有文件。

RN 默认开发检查及配置模板以 `uni-rn-dev/references/quality.md` 和 `uni-rn-dev/templates/quality/` 为维护源；修改后运行 `python scripts/sync_rn_quality.py`，同步到 RN 库和 GitHub 交付技能的独立副本，再用 `--check` 核对。消费者无需安装其他技能，也不读取技能仓根目录脚本。质量模板按目标工程合并采用，不覆盖已有工具链、规则和有效例外，不自动迁移其他仓库。

模板的真实工具回归使用 `npm ci --prefix tests/fixtures/rn-quality --ignore-scripts --no-audit --no-fund` 安装锁定的隔离工具，再运行 `node --test tests/rn-quality.test.cjs`。覆盖规则正反例、库声明输出、格式及实际提交钩子的拦截、放行和部分暂存保护；这些结果不替代 RN 应用构建或设备验收。

使用[评测任务](evals/cases.md)检查实际输出、独立使用和任务边界，再核对格式、相对引用及插件清单。行为运行记录放在仓库外；计划和设计保留在 `docs/`，不进入技能默认上下文。

[RN 平台独立使用](evals/rn-platform-ownership.md)覆盖 iOS 安装调试和变更验证范围，核对通用流程不依赖企业技能。

### 联合发现评测

`evals/joint-discovery/` 维护 Uni 与 Unif 同时可用时的专项发现题库和冻结目录。目录包含两个包的全部技能名称与触发描述，题目检查应组合使用的技能及应排除的误选，不将两层设为互斥选择。该评测独立于现有单包题库。

[候选联合题目](evals/joint-discovery/cases.next.json)覆盖当前两仓的任务入口。正式评测仍采用同批冻结的 `catalog.json` 和 `cases.json`。取得两仓来源提交后，用 `freeze --catalog` 将新目录写至临时文件，通过 `validate --catalog <新目录> --suite evals/joint-discovery/cases.next.json` 核对，再一并替换正式目录和题目，同步到 Unif。

离线校验只读取仓内冻结资料，不需要安装 Unif、访问其他私有仓或调用模型：

```sh
.venv/bin/python -m scripts.joint_discovery_eval validate
```

核对候选目录时提供两仓路径和完整提交 SHA。将以下示例路径和修订替换为实际值，三条命令共用同一个仓外目录文件。

```sh
.venv/bin/python -m scripts.joint_discovery_eval freeze \
  --catalog /tmp/uni-unif-candidate-catalog.json \
  --uni-repo /path/to/uni-skills --uni-ref UNI_COMMIT_SHA \
  --unif-repo /path/to/unif-portal-dev-skills --unif-ref UNIF_COMMIT_SHA
.venv/bin/python -m scripts.joint_discovery_eval verify-sources \
  --catalog /tmp/uni-unif-candidate-catalog.json \
  --uni-repo /path/to/uni-skills --unif-repo /path/to/unif-portal-dev-skills
.venv/bin/python -m scripts.joint_discovery_eval validate \
  --catalog /tmp/uni-unif-candidate-catalog.json --suite evals/joint-discovery/cases.next.json
```

真实模型运行使用[行为评测配置](evals/behavior/README.md)，显式启用并配置模型、服务地址、凭据和请求预算，每次使用新的仓库外输出目录：

```sh
SKILL_EVAL_ENABLED=true .venv/bin/python -m scripts.joint_discovery_eval run \
  --output /tmp/uni-unif-joint-discovery
```

缺少运行条件或样本不完整时报告证据不足，不计为通过。离线校验只证明题库与目录一致；模型选择结果不代替宿主实际加载或业务验收。

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
