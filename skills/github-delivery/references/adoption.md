# 接入与同步

## 选择采用范围

先确认 owner/repo、包身份、技术栈、默认分支、已有工作流与授权。自带模板是 RN 库交付基线，使用 Yarn、Turbo、release-it、npm OIDC，以及真实 iOS/Android 宿主；不能据此给普通 Web、后端或鸿蒙项目增加这些依赖。

工程采用组织约定时，先将所属组织提供的非敏感配置落实为 `.github/organization.json`；通用工具只读取该工程文件，不查找其他技能的安装目录。配置可声明 owner、包名约束、Pages 规则、发布 App ID、仓库设置、安全策略和已停用自动化；省略的组织策略不由工具推定。

新库先具备实际构建、测试、原生宿主和包清单，再同步模板。组织名、包名、Pages 地址从显式 owner/repo 与 package.json 取得，不要求特定 scope 或 react-native- 名称。现有源码、锁文件、发布绑定和项目专用 `.github/ci/` 脚本继续按本库契约维护。

在本技能目录执行：

```sh
bash scripts/sync-repo.sh example/widget /absolute/path/to/widget
bash scripts/check-repo.sh example/widget /absolute/path/to/widget
```

同步只改目标工作树，不提交或修改远端。`--check` 只读核对；缺依赖或模板不一致时返回非零。新库若没有可用的 release-it/Turbo 接线，补齐本库配置后重新检查，不能把已写入 workflow 当作接入完成。

## 采用记录与更新

同步生成 `.github/delivery.json`，记录来源摘要、包身份、实际结构、受管文件与 AGENTS 管理块摘要。来源始终在本技能；消费仓的工作流和脚本为可执行产物。CI 使用：

```sh
node .github/scripts/check-delivery.cjs
```

该检查无需技能安装或网络下载，核对已采用文件、工作流依赖、包开发元数据、原生/站点结构变化和已停用配置。它不检查远端最新标准，也不替代真实构建、产物与消费者验证。

升级时从新的技能来源重新同步，审查差异并走工程已有 PR 流程。`.github/delivery.json` 与生成文件一起提交，不单独手改摘要以绕过失败。

确有项目专用工作流时，在采用记录的 `projectFiles` 中列出实际专用的 `ci.yml`、`release.yml`、`deploy-docs.yml`、`native-lint.yml` 或 `nightly-build-check.yml` 的仓库相对路径；同步保留该文件并刷新采用摘要，`--check` 与 CI 仍核对已提交内容是否漂移。此入口仅保留上述项目工作流，不能豁免校验器、actions 或其他模板，CI 必须保留仓内交付检查接线。初次迁移应先审查并完成必要的仓内检查接线，再生成记录。

## 保留的项目内容

AGENTS 只更新既有管理块，其他内容保留。PR 模板、审查配置、安全政策和功能请求模板只在缺失时创建，不覆盖本库政策。站点与原生检查按真实目录/源码选择；自有 LLM builder 和专属测试保留，共享实现由同一来源同步。

已有 PR Agent 服务继续使用其配置；新库仅在明确选择后传 `--pr-agent`。启用服务、提供密钥或调整远端权限不属于普通模板同步。

共享文件漂移在来源修复后重新下发。符号链接、重复管理块或无效包身份导致失败时，先核对目标与归属，不强行覆盖。应用模式可能已完成部分文件更新再报告接入缺项，失败后检查工作树；检查模式始终不写文件。
