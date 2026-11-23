# CI 自包含行为题库

本目录为 Uni Skills 的只读 CI 评测输入，覆盖本包 13 个技能的发现正例、发现反例和内容应用。原任务材料与人工判据见[评测任务](../cases.md)。

## 选题范围

默认 `scope=affected`，按固定基线与候选的实际变化选题；`scope=all` 明确选择整份题库。选题范围由 `scope` 决定，`full` 只决定重复次数。

- 技能源与分包内的同名生成副本映射到同一技能，只评一次。单纯版本字段或来源摘要、行段记录变化不扩大模型评测范围，分发一致性仍由仓库校验负责。
- 技能正文与配套资料变化选择该技能的题目；名称、触发描述或可见技能集合变化，再覆盖明确声明的跨技能发现约束。其他技能的发现题只读取目录元数据，不因无关正文变化重跑。
- 插件元数据或市场映射变化按受影响包的成员选题；题库内容变化定位到变动题目。共用评测器或其工作流变化覆盖全库，普通 CI、历史资料或生成脚本变化本身不启动全库模型调用。
- 摘要记录本次范围与实际覆盖数量；未选技能标为未评测，不将其计作失败，也不声称本次覆盖全库。已选题缺样本、执行错误与统计证据不足仍如实保留。

## 覆盖与执行边界

| 模式 | 题数 | 作答模型可见资料 |
| --- | ---: | --- |
| application | 23 | 一个完整的目标技能目录、题面与题内 fixtures |
| discovery_positive | 16 | 本包技能的 name/description、题面与题内事实 |
| discovery_negative | 15 | 本包技能的 name/description、题面与题内事实 |

合计 54 题。代码变更题覆盖普通实现、重构、状态与授权。故障诊断题要求从网关错误追到实例配置，代码审查题要求从差异定位跨账号清理，变更验证题要求识别遗漏的动态消费者及失效的验证记录。测试设计覆盖新功能和存量系统，RN 覆盖宿主、生命周期与局部更新，技能编写覆盖独立分发及触发边界，并检验维护者从混合材料写出的完整正文是否可读、保真且独立于讨论。

每项技能均覆盖三种模式。应用题只提供该技能目录、其中的必要资料和题内 fixtures。题内 `AGENTS.md`、接口、diff 和运行记录是匿名合成材料，模型不能访问其他私有仓库、本机凭据或真实服务。

发现题只向作答者提供该修订实际存在的名称与描述，样本记录目录摘要。必选、禁选集合以外的技能不按加载数计错。如何取基线、是否比较升降，取决于同一题的判据能否用于两边。

| 条件 | 取证方式 |
|---|---|
| 应用题的两版都有当前技能名 | 各读该版同名正文，使用同一题面、材料和判据进行配对。 |
| 基线缺当前名，题目明确登记了实际存在的前身 | 基线读 `baseline_skill` 的原目录，候选读当前目录。样本的 `skill` 和读取轨迹记录各自实际使用的技能。 |
| 应用题基线缺当前名，且明确登记了 `null` 或登记的前身也不存在 | 仅运行候选，保存答卷、读取轨迹和逐项判据。报告显示候选完成数和缺少的基线，完整配对为零。 |
| 应用题基线缺当前名，题目省略 `baseline_skill` | 保留原有配对要求。该题记录基线不足，不发送模型请求。 |
| 发现题任一必选、禁选名在基线不存在 | 仅运行候选，记录实际选择、目录和判据，不将名称的增减计为效果变化。 |

候选单侧样本可以证明这次的实际作答，无法判定相对改善、退化或持平。损坏的文件、符号链接和无法读取的目录仍按输入错误处理。

应用题由独立上下文依据冻结 `rubric` 逐项审阅完整回答与读取轨迹，判据不交给作答模型。判据检查具体状态归属、实际消费者、异常/取消时序、授权及证据范围；只出现关键词或正确复述标题不能算通过。模型评阅需保留理由并人工抽查。

## 文件格式

`cases.json` 根为 `formatVersion: 1` 和 `cases` 数组。每题包含：

| 字段 | 用途 |
| --- | --- |
| id、skill、mode | 稳定题号、所属技能、模式 |
| baseline_skill | 仅用于应用题。明确前身填旧技能名，明确没有前身填 JSON 的 `null`。省略时要求同名配对。三种情况都优先基线中的当前名。 |
| prompt | 自然请求及只读范围 |
| fixtures | 相对路径到 UTF-8 文本的映射；运行时置于 `fixtures/` 下 |
| rubric | 不向作答模型公开的语义判据 |
| required_skills、forbidden_skills | 发现模式的本包集合约束 |
| source | 原有题文件/编号、固定来源与适配范围 |

应用技能由运行器置于 `skills/<实际技能名>/`。资料路径必须相对、唯一且不能穿越目录。题目可以在源代码或文字中展示合成路径，但不会取得对应真实资源。

## 来源与维护

依据本仓任务题及补充场景提供 CI 匿名 fixtures，保留题意、契约与语义判据，覆盖范围见上表，发现集合限定本包。每题 `source` 指向原有题文件及对应技能场景，并说明适配范围。既有命名、生成类型、实例状态、跨轮结果、资源交接、独立产物消费、交付授权和文档证据边界仍由原题语义约束。

变更题目时同时核对题面、fixtures、判据和来源。比较候选与基线时使用同一份题库、模型与判据；题库、素材或模型变化后不能把结果直接拼成趋势。新增技能应补齐正例、反例和应用题，不以更多易题替代原有边界。

CI 这里只观察固定资料下的发现与书面应用。真实宿主自动加载、源码实施、完整测试、归档构建、独立消费者、设备及真实业务仍需各自评测。未执行、缺配置或资料不足应保留为证据不足，不能记成行为通过。

## 运行与报告

打开[模型评测运行记录](https://github.com/unif-skill/uni-skills/actions/workflows/behavior-eval.yml)，按提交、分支和触发方式选择对应运行：

1. 运行中展开 **Evaluate skill behavior → Compare baseline and candidate behavior** 的实时日志：每次尝试后显示进度、完整配对数和耗时，可对照的样本另显示观察升降；每题完成后显示逐题结论。请求日志显示编号、作答/评阅、耗时和重试等待，不输出请求内容或凭证。单对观察不代表最终效果结论。
2. 运行结束后，在 **Summary** 下方查看评测结论、完成配对、实际请求次数和步骤退出码。
3. 在 **Artifacts** 下载 `behavior-eval-<run_id>-<attempt>`，解压后查看 `artifacts/behavior-eval/summary.md`、`summary.json`、`workflow.json` 及 `traces/`。产物保留 30 天。
4. 使用有仓库读取权限的 GitHub 账号；未登录或无权限时可能显示 404。

模型步骤和作业允许失败，不是发布门禁。绿色工作流只表示工作流按其配置结束，不能代替报告中的改善、退化、持平或证据不足。退出码 `0` 表示完成或无相关变化，`1` 表示退化，`2` 表示证据不足；没有相关题目时明确跳过。持平只表示本次样本未观察到差异，不保证其他任务的效果。

“先前 API 传输失败，本次停止调用”表示该样本没有继续发请求。实际传输失败次数（含重试）单独汇总，逐次证据保存在 `api_trace`。相同错误在 Markdown 中合并计数并链接代表样本，JSON 和 traces 保留完整记录；不能把停调后的样本数当成 HTTP 失败次数。报告中的 traces 相对链接需下载并解压产物后使用。

## 触发与重复次数

[工作流源码](../../.github/workflows/behavior-eval.yml)在 PR、main 的技能、题库、分发入口或评测工具变化时运行。`smoke` 每题运行 1 轮，`full` 运行 10 轮。可比较时每轮各运行基线和候选一次，单侧取证时仅运行候选。PR 的 `auto` 使用 `smoke`；main 推送及手动 `auto` 遇到比较范围中的 `feat` 提交或根清单 major／minor 提升时使用 `full`，其余使用 `smoke`。无受影响题目时直接跳过。

手动运行指定 `scope`、`mode`、基线 `base_ref` 和候选 `head_ref`。候选留空时使用工作流修订；调整评测运行器时可固定被测候选，避免改变技能内容。PR 的基线为目标分支 `base.sha`，main 推送为 `before`，手动未填时为 `HEAD^`；基线不可解析时报告证据不足，不回退为候选自比。

每次对照使用同一题库、模型、判据与运行设置，分别启动独立上下文。`full` 的 10 对按每题每判据做双侧配对 sign test（p ≤ 0.05，至少 5 对），不将其他增益抵消观察到的下降。逐判据结论未做多重比较校正，不作为统计保证或生产准确率。

## 模型配置

在仓库 **Settings → Secrets and variables → Actions** 按下表配置；变量写入 **Variables**，API Key 写入 **Secrets**。同名 Secret 不能代替工作流读取的 Variable。

| 配置 | 类型 | 用途 |
|---|---|---|
| `SKILL_EVAL_ENABLED` | variable | 设为 `true` 才启用模型调用 |
| `SKILL_EVAL_MODEL` | variable | 百炼答题模型标识，例如 `deepseek-v4-pro` |
| `SKILL_EVAL_JUDGE_MODEL` | variable，可选 | 评阅模型；未填时用答题模型的独立上下文 |
| `SKILL_EVAL_MAX_REQUESTS` | variable | 单次运行的总 API 请求次数上限，包含答题、评阅与重试；不是美元预算 |
| `SKILL_EVAL_MAX_OUTPUT_TOKENS` | variable，可选 | 单次输出 Token 上限，128–16384，默认 4096；推理模型的预算可能同时包含思考与正文，截断结果不能作为完整答案 |
| `SKILL_EVAL_TIMEOUT_SECONDS` | variable，可选 | 单次 API 请求等待上限，1–300 秒，默认 60 秒；不改变题目、模型与判据 |
| `UNIF_MODEL_BASE_URL` | variable | 百炼兼容接口地址：`https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `UNIF_MODEL_API_KEY` | secret | 百炼 API Key；无需 OpenAI 或 DeepSeek 官网 Key，不使用本机 OAuth 或用户订阅鉴权 |
| `SKILL_EVAL_MAX_WORKERS` | variable，可选 | 同时运行的题目数，1–3，默认 3；服务不稳定时可降低并发 |
| `SKILL_EVAL_RETRY_BASE_SECONDS` | variable，可选 | 503 首次重试的等待秒数，1–30，默认 1；第二次等待为其两倍 |

缺配置、外部 fork PR 无密钥、预算耗尽或样本不完整时报告证据不足。外部 fork PR 不注入模型密钥。

HTTP 503 按[服务端错误说明](https://help.aliyun.com/zh/model-studio/error-code)最多重试两次，每次尝试均计入总请求预算并保留轨迹。等待时间按 `SKILL_EVAL_RETRY_BASE_SECONDS` 的一倍、两倍执行；重试耗尽或其他传输错误停止后续调用，未返回的 Token 用量保持未知。输出截断、拒答或无效评分不自动重试，也不作为完整样本。

总请求上限、180 分钟作业超时和同 ref 取消旧运行共同限制规模，不承诺实际费用。写入配置不表示模型权限、兼容响应或服务可用性已经验证。

## 本地校验与运行

从仓库根目录执行，将 `BASE_SHA`、`HEAD_SHA` 设为实际比较修订。最后一条命令仅在显式启用并提供上述配置后调用模型，输出放在仓库外：

```sh
python scripts/sync_evaluation_tools.py --verify
python scripts/behavior_eval.py validate --root .
python scripts/behavior_eval.py plan --repo . --base "$BASE_SHA" --head "$HEAD_SHA" --scope affected --mode smoke --event workflow_dispatch --output /tmp/skill-eval-plan.json
python scripts/behavior_eval.py run --plan /tmp/skill-eval-plan.json --output-dir /tmp/skill-eval-artifacts --progress
```

评测器、测试与工作流由 Uni 单一维护，Unif 显式采用同源副本；各仓 CI 只使用仓内文件，不读取其他私有仓或本机安装。
