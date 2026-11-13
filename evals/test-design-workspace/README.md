# 草稿编辑器修改回放

维护者可用这个离线小工程观察 agent 如何应用 `uni-test-design` 修改源码和测试。需要 Node.js 22.18 或更高版本。每次从相同起点复制，只把工程、下列任务和本轮指定的技能交给作答 agent，验收文件由维护者保管。

从 Uni 仓根目录创建副本并运行原有测试。

```sh
case_dir=evals/test-design-workspace
run_dir=$(mktemp -d)
cp -R "$case_dir/project" "$run_dir/project"
cp -R skills/uni-test-design "$run_dir/uni-test-design"
(cd "$run_dir/project" && node --test test/*.test.mts)
```

给作答 agent 的任务如下。

> 请采用给定的 uni-test-design，在这个送货草稿编辑器里修复切换账号后偶现回执串到另一份草稿的问题。团队也希望整理遗留兼容和无效测试，已经确认没有支持责任的可以直接删除。请按工程资料判断取舍，实际修改源码和回归测试，执行本地验证并说明依据。限这个离线副本。

agent 完成后，在同一个 shell 内分别检查项目测试、独立行为和文件差异。

```sh
(cd "$run_dir/project" && node --test test/*.test.mts)
node "$case_dir/verify.mjs" "$run_dir/project"
diff -ru "$case_dir/project" "$run_dir/project"
```

初始工程自带的两个测试都通过。五个独立探针中有两个会复现串写，分别覆盖切到另一账号，以及切换后又回到原账号才收到旧回执。修复后五个探针应全部通过，`diff` 发现改动时退出码为 1。结合差异核对以下两项。

- 沿公开编辑入口核实输入形状，查看无消费者的内部 `replacement` 分支和仅靠强转调用它的测试是否一并删除。该分支从公开入口不可达，留着它也能通过独立探针。检查正常编辑用例是否只用约定的 `{body}` 输入，避免用正例固定 `body` 与旧字段 `replacement` 并存时尚未约定的处理方式。
- 检查新增回归能否独立暴露错误。旧库存样本须经真实恢复入口读取。迟到回执须在实际发送后挂起，切换账号再释放，观察旧操作结局与新账号状态，并验证正常提交。可把 agent 的测试组合到新的初始工程再运行，观察原异步缺陷被哪项用例捕获。测试只改断言、使用固定延时或替身自行返回预期结果均缺少对应证据。

记录实际读取的技能、改动和各项验证结果，原始运行产物留在临时目录。比较技能前后效果时，用相同初始工程与任务分别开独立上下文，只更换技能条件。一次修改回放只能说明该样本的行为。
