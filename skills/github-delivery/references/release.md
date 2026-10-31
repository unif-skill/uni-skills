# 发布与恢复

沿用目标工程的包身份、发布工具与授权。源码接入、公开发行准备、实际发布和发布后验收是不同阶段；只交付本地候选时不提前建站、改许可、配置远端或发布。

## 检查入口

在已接入的消费仓运行：

| 阶段 | 命令 | 证据 |
|---|---|---|
| 开发接入 | `node .github/scripts/check-delivery.cjs` | 采用文件、工作流依赖和开发元数据 |
| 实际打包 | `node .github/scripts/check-library.cjs pack` | 真实 tarball 的身份、公开出口、类型、资源及安全路径 |
| 公开发行前置 | `node .github/scripts/check-library.cjs release` | 许可、README、站点和发布配置 |
| 已发布版本 | `node .github/scripts/check-library.cjs published` | registry 精确版本、下载产物和完整性 |

检查器内置公开 npm 发行基线，`pack` 禁止安装/打包生命周期脚本。发行站点要求只作用于明确采用此公开交付契约的库；其他分发目标使用自身现有工具，不擅自改变 registry 或公开范围。

## 身份与版本

自带 release 模板用 npm OIDC 发布，用目标工程既有 GitHub App 推送版本提交与标签。核对 npm Trusted Publisher 的 owner/repo、workflow 与环境，以及工程组织配置的发布 App ID、`RELEASE_APP_ID`、`RELEASE_APP_PRIVATE_KEY` 和分支保护；组织配置与变量同时存在时必须一致；身份配置不随模板自动创建。

查询超时、404 或空列表不证明版本未占用。常规采用 patch/minor，major 需明确授权；自动版本判定遇到 major 应中止，不能用试发探测注册表。工作流名、权限、发布事件和 concurrency 保持项目契约，避免发版提交循环触发。

## 恢复与验收

发布成功后记录实际 revision/version，以该提交重新检出并验证精确版本。站点通过版本索引核对，HTTP 200 不证明已部署本次版本。

已有版本验收失败时，先定位 registry 延迟、包内容或站点问题；使用工作流 `verify_only` 恢复检查与文档部署，不再次发布相同或不必要的新版本。重试有界，并保留最终失败。

真实 tarball 检查不能代替独立消费者类型/运行验证，也不能代替原生设备或真实服务。SDK 补丁继续由项目已确认的归属方维护，迁移 CI 不改变补丁分发和宿主责任。
