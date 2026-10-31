# 仓库设置与分支保护

先核对当前仓库、默认分支与真实注册的检查，再调整远端。模板包含合并策略、安全设置和 RN 检查名称；工程未采用此基线时，不把模板直接套到其他技术栈。

```sh
bash scripts/setup-repo.sh example/widget --target-path /path/to/widget --check
```

`--check` 只读。缺权限、必需检查尚未注册、多个同名 ruleset 或无法取得关键配置时失败，不先写远端再猜结果。应用模式不带 `--check`，需要本次任务明确授权，并在修改后回读核对。

发布 App 必须属于目标工程已批准的发布身份。已有 bypass actors、额外检查和非受管规则保留；新建保护且缺少可直接推送的发布 Integration 时，明确提供真实 App ID：

```sh
bash scripts/setup-repo.sh example/widget --target-path /path/to/widget --release-app-id 123456 --check
```

核对 App 安装范围、仓库变量和 private key 来源后，再执行获准的应用操作。工具不创建 App、不搬运私钥，不把模板作者的 App ID 赋给其他项目。已有同 ID 的受限 bypass 不能自动放宽。

组织的仓库设置和安全策略从目标工程 `.github/organization.json` 取得，省略项保留远端现状。必需检查从工程已采用的 `.github/delivery.json` 取得，既有远端额外检查继续保留。安全功能变化须在本次授权内，不因技能安装而修改远端。

组织默认贡献/安全文件的自动继承仍是 GitHub `.github` 特殊仓库功能；它与本技能的交付标准分开。保留该功能的组织可继续维护默认文件，不因此让 CI 依赖旧工程标准仓。
