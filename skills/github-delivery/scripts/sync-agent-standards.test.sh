#!/usr/bin/env bash

# shellcheck disable=SC2016
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sync_script="$script_dir/sync-agent-standards.sh"
begin_marker='<!-- BEGIN GITHUB DELIVERY STANDARD -->'
end_marker='<!-- END GITHUB DELIVERY STANDARD -->'
workspace="$(mktemp -d)"
trap 'rm -rf "$workspace"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

file_mode() {
  local mode
  if mode="$(stat -f '%Lp' "$1" 2>/dev/null)"; then
    printf '%s\n' "$mode"
  else
    stat -c '%a' "$1"
  fi
}

assert_managed_block() {
  local file="$1"
  local begin_count end_count
  begin_count="$(awk -v marker="$begin_marker" '$0 == marker { n++ } END { print n + 0 }' "$file")"
  end_count="$(awk -v marker="$end_marker" '$0 == marker { n++ } END { print n + 0 }' "$file")"
  [[ "$begin_count" -eq 1 && "$end_count" -eq 1 ]] || fail '共享区块未保持唯一完整边界'
  if grep -Eq '\{\{[^}]+\}\}' "$file"; then fail '生成入口保留未渲染变量'; fi
}

# 普通仓库名和非 Unif 包名可独立接入；未存在的开发文档不生成链接。
target="$workspace/portable-package"
mkdir -p "$target"
printf '{"name":"@example/mobile-widget"}\n' >"$target/package.json"
cat >"$target/AGENTS.md" <<'EOF'
# Mobile Widget

## 本仓规则

保留本仓说明和 `符号 & 路径`。
EOF
chmod 0600 "$target/AGENTS.md"
cp "$target/AGENTS.md" "$workspace/before.md"
if bash "$sync_script" --check Mobile.Widget "$target" >/dev/null 2>&1; then
  fail '未接入时 check 应报告缺失'
fi
cmp -s "$workspace/before.md" "$target/AGENTS.md" || fail 'check 修改了未接入的文件'
bash "$sync_script" Mobile.Widget "$target"
assert_managed_block "$target/AGENTS.md"
grep -Fq 'Mobile.Widget' "$target/AGENTS.md" || fail '未写入当前仓库名'
grep -Fq '@example/mobile-widget' "$target/AGENTS.md" || fail '未使用真实包名'
grep -Fq '保留本仓说明和 `符号 & 路径`。' "$target/AGENTS.md" || fail '覆盖了本仓说明'
if grep -Fq 'docs/DEVELOPMENT.md' "$target/AGENTS.md"; then fail '链接了不存在的开发文档'; fi
if grep -Eq 'unif-portal-dev-skills|unif-design/|\.\./skills/' "$target/AGENTS.md"; then
  fail '通用入口仍绑定旧插件或兄弟仓库'
fi
[[ "$(file_mode "$target/AGENTS.md")" == 600 ]] || fail '同步改变了 AGENTS.md 权限'
bash "$sync_script" --check Mobile.Widget "$target"

# 默认目标为调用时的当前目录；同步幂等。
cp "$target/AGENTS.md" "$workspace/synced.md"
(cd "$target" && bash "$sync_script" Mobile.Widget)
cmp -s "$workspace/synced.md" "$target/AGENTS.md" || fail '重复同步不幂等'

# 开发资料出现后，check 报告漂移但不写入；同步后只替换管理块。
mkdir "$target/docs"
printf '# Development\n' >"$target/docs/DEVELOPMENT.md"
if bash "$sync_script" --check Mobile.Widget "$target" >/dev/null 2>&1; then
  fail '开发资料入口变化未被 check 检出'
fi
cmp -s "$workspace/synced.md" "$target/AGENTS.md" || fail 'check 写入了开发资料入口'
bash "$sync_script" Mobile.Widget "$target"
grep -Fq '(docs/DEVELOPMENT.md)' "$target/AGENTS.md" || fail '存在的开发资料未生成链接'
[[ "$(file_mode "$target/AGENTS.md")" == 600 ]] || fail '替换区块改变了文件权限'

# 已有区块原位替换，前后未管理内容逐字保留。
cat >"$target/AGENTS.md" <<'EOF'
# Existing Repository

管理块前的说明。
<!-- BEGIN GITHUB DELIVERY STANDARD -->
stale managed text
<!-- END GITHUB DELIVERY STANDARD -->

## 本仓规则
管理块后的说明。
EOF
cat >"$workspace/unmanaged.md" <<'EOF'
# Existing Repository

管理块前的说明。

## 本仓规则
管理块后的说明。
EOF
bash "$sync_script" Mobile.Widget "$target"
assert_managed_block "$target/AGENTS.md"
awk -v begin="$begin_marker" -v end="$end_marker" '
  $0 == begin { managed = 1; next }
  $0 == end { managed = 0; next }
  !managed { print }
' "$target/AGENTS.md" >"$workspace/after-unmanaged.md"
cmp -s "$workspace/unmanaged.md" "$workspace/after-unmanaged.md" || fail '修改了管理块外正文或位置'
if grep -Fq 'stale managed text' "$target/AGENTS.md"; then fail '未替换过期管理块'; fi

# 仍在采用旧 marker 的库沿用同一管理块，不要求包名和仓库名一致。
printf '{"name":"@unif/react-native-camera"}\n' >"$target/package.json"
bash "$sync_script" camera-source "$target"
assert_managed_block "$target/AGENTS.md"
grep -Fq '@unif/react-native-camera' "$target/AGENTS.md" || fail '未保留真实包身份'

# 没有 AGENTS.md 时创建入口，使用默认文件权限。
new_target="$workspace/new-package"
mkdir "$new_target"
printf '{"name":"plain-mobile-package"}\n' >"$new_target/package.json"
bash "$sync_script" mobile-package "$new_target"
assert_managed_block "$new_target/AGENTS.md"
[[ "$(file_mode "$new_target/AGENTS.md")" == 644 ]] || fail '新入口权限不正确'

# 不完整、重复、嵌套、倒序 marker 和无 H1 的未管理正文必须在写入前拒绝。
for invalid in missing-end missing-begin duplicate nested reverse no-heading; do
  invalid_target="$workspace/$invalid"
  mkdir "$invalid_target"
  printf '{"name":"plain-mobile-package"}\n' >"$invalid_target/package.json"
  case "$invalid" in
    missing-end) printf '# Invalid\n%s\ntext\n' "$begin_marker" ;;
    missing-begin) printf '# Invalid\n%s\n' "$end_marker" ;;
    duplicate) printf '# Invalid\n%s\n%s\n%s\n%s\n' "$begin_marker" "$end_marker" "$begin_marker" "$end_marker" ;;
    nested) printf '# Invalid\n%s\n%s\n%s\n%s\n' "$begin_marker" "$begin_marker" "$end_marker" "$end_marker" ;;
    reverse) printf '# Invalid\n%s\n%s\n' "$end_marker" "$begin_marker" ;;
    no-heading) printf '正文没有一级标题。\n' ;;
  esac >"$invalid_target/AGENTS.md"
  cp "$invalid_target/AGENTS.md" "$workspace/before-invalid.md"
  if bash "$sync_script" mobile-package "$invalid_target" >/dev/null 2>&1; then fail "接受了无效边界: $invalid"; fi
  cmp -s "$workspace/before-invalid.md" "$invalid_target/AGENTS.md" || fail "拒绝前写入了无效边界: $invalid"
done

# AGENTS.md 符号链接不能被替换，链接目标不能被写入。
link_target="$workspace/link-target"
mkdir "$link_target"
printf '{"name":"plain-mobile-package"}\n' >"$link_target/package.json"
printf '# External\n保持原文。\n' >"$workspace/external.md"
cp "$workspace/external.md" "$workspace/before-external.md"
ln -s "$workspace/external.md" "$link_target/AGENTS.md"
if bash "$sync_script" mobile-package "$link_target" >/dev/null 2>&1; then fail '接受了 AGENTS.md 符号链接'; fi
[[ -L "$link_target/AGENTS.md" ]] || fail '替换了 AGENTS.md 符号链接'
[[ "$(readlink "$link_target/AGENTS.md")" == "$workspace/external.md" ]] || fail '修改了链接地址'
cmp -s "$workspace/before-external.md" "$workspace/external.md" || fail '修改了链接目标'

# manifest.name 必须为非空字符串；错误不能留下半成品。
for invalid_name in '{}' '{"name":""}' '{"name":"   "}' '{"name":123}' 'invalid json'; do
  printf '%s\n' "$invalid_name" >"$new_target/package.json"
  cp "$new_target/AGENTS.md" "$workspace/before-name.md"
  if bash "$sync_script" mobile-package "$new_target" >/dev/null 2>&1; then fail "接受了无效包名: $invalid_name"; fi
  cmp -s "$workspace/before-name.md" "$new_target/AGENTS.md" || fail '包名校验失败仍修改了入口'
done

legacy="$workspace/legacy"
mkdir "$legacy"
printf '{"name":"@example/widget"}\n' >"$legacy/package.json"
cat >"$legacy/AGENTS.md" <<'EOF'
# Legacy project
Before.
<!-- BEGIN UNIF REACT NATIVE STANDARD -->
Old cross-plugin instructions.
<!-- END UNIF REACT NATIVE STANDARD -->
After.
EOF
cp "$legacy/AGENTS.md" "$workspace/legacy-before.md"
if bash "$sync_script" --check widget "$legacy" >/dev/null 2>&1; then fail '旧区块迁移前不能通过 check'; fi
cmp -s "$legacy/AGENTS.md" "$workspace/legacy-before.md" || fail '旧区块检查写入了文件'
bash "$sync_script" widget "$legacy"
assert_managed_block "$legacy/AGENTS.md"
if grep -Fq 'UNIF REACT NATIVE STANDARD' "$legacy/AGENTS.md"; then fail '旧管理块仍然保留'; fi
if grep -Fq 'Old cross-plugin instructions' "$legacy/AGENTS.md"; then fail '旧指令仍然保留'; fi
if ! grep -Fxq 'Before.' "$legacy/AGENTS.md" || ! grep -Fxq 'After.' "$legacy/AGENTS.md"; then fail '旧区块以外内容丢失'; fi
bash "$sync_script" --check widget "$legacy"
for mode in mixed incomplete duplicate; do
  cp "$workspace/legacy-before.md" "$legacy/AGENTS.md"
  case "$mode" in
    mixed) sed 's/END UNIF REACT NATIVE/END GITHUB DELIVERY/' "$legacy/AGENTS.md" > "$workspace/invalid.md" ;;
    incomplete) sed '/END UNIF REACT NATIVE/d' "$legacy/AGENTS.md" > "$workspace/invalid.md" ;;
    duplicate) cat "$legacy/AGENTS.md" "$workspace/synced.md" > "$workspace/invalid.md" ;;
  esac
  cp "$workspace/invalid.md" "$legacy/AGENTS.md"
  if bash "$sync_script" widget "$legacy" >/dev/null 2>&1; then fail "无效旧区块被接受: $mode"; fi
  cmp -s "$legacy/AGENTS.md" "$workspace/invalid.md" || fail '失败时覆盖了无效旧区块'
done

printf 'PASS: portable agent entry, legacy migration, managed boundaries, permissions and read-only checks\n'
