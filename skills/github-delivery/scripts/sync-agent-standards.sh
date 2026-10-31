#!/usr/bin/env bash

set -euo pipefail

begin_marker='<!-- BEGIN GITHUB DELIVERY STANDARD -->'
end_marker='<!-- END GITHUB DELIVERY STANDARD -->'
# 已发布消费者仍可能使用旧区块；同步时原位迁移，不保留第二份指令。
legacy_begin='<!-- BEGIN UNIF REACT NATIVE STANDARD -->'
legacy_end='<!-- END UNIF REACT NATIVE STANDARD -->'
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template="$script_dir/../templates/AGENTS.md"

usage() {
  printf 'Usage: %s [--check] <repo-name> [target-path]\n' "${0##*/}" >&2
  exit 2
}

file_mode() {
  local mode
  if mode="$(stat -f '%Lp' "$1" 2>/dev/null)"; then
    printf '%s\n' "$mode"
  elif mode="$(stat -c '%a' "$1" 2>/dev/null)"; then
    printf '%s\n' "$mode"
  else
    return 1
  fi
}

check_only=false
if [[ "${1:-}" == --check ]]; then check_only=true; shift; fi
[[ $# -ge 1 && $# -le 2 ]] || usage

repo_name="$1"
target_dir="${2:-$PWD}"

[[ "$repo_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || usage

agents_file="$target_dir/AGENTS.md"
package_file="$target_dir/package.json"

if [[ -L "$agents_file" ]]; then
  printf 'Refusing to replace symlink: %s\n' "$agents_file" >&2
  exit 1
fi
[[ -f "$template" && -f "$package_file" ]] || exit 1

actual_package="$(node -e '
  const fs = require("fs");
  const name = JSON.parse(fs.readFileSync(process.argv[1], "utf8")).name;
  if (typeof name !== "string" || !name.trim()) throw new Error("Target package.json must have a non-empty name");
  process.stdout.write(name);
' "$package_file")" || exit 1
development_entry=''
if [[ -f "$target_dir/docs/DEVELOPMENT.md" ]]; then
  development_entry='项目设计、约定和实现入口见[开发资料](docs/DEVELOPMENT.md)。'
fi
temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT
input_file="$agents_file"
agents_mode=644
if [[ -f "$agents_file" ]]; then
  agents_mode="$(file_mode "$agents_file")" || exit 1
else
  input_file="$temp_dir/input.md"
  printf '# %s 开发入口\n' "$repo_name" > "$input_file"
fi

if ! begin_count="$(awk -v begin="$begin_marker" -v end="$end_marker" -v old_begin="$legacy_begin" -v old_end="$legacy_end" '
  $0 == begin || $0 == old_begin {
    current_end = ($0 == begin ? end : old_end)
    begin_count++
    if (state != 0) invalid = 1
    state = 1
    next
  }
  $0 == end || $0 == old_end {
    end_count++
    if (state != 1 || $0 != current_end) invalid = 1
    state = 2
  }
  END {
    if (invalid || begin_count != end_count || begin_count > 1 || state == 1) exit 1
    print begin_count
  }
' "$input_file")"; then
  exit 1
fi

rendered="$temp_dir/rendered.md"
updated="$temp_dir/AGENTS.md"

node - "$template" "$repo_name" "$actual_package" "$development_entry" >"$rendered" <<'NODE'
const fs = require('node:fs');
const [template, repo, packageName, development] = process.argv.slice(2);
const values = { REPO: repo, PACKAGE: packageName, DEVELOPMENT_ENTRY: development };
process.stdout.write(fs.readFileSync(template, 'utf8').replace(
  /\{\{(REPO|PACKAGE|DEVELOPMENT_ENTRY)\}\}/g, (_, key) => values[key]
));
NODE

if [[ "$begin_count" -eq 1 ]]; then
  awk -v begin="$begin_marker" -v end="$end_marker" -v old_begin="$legacy_begin" -v old_end="$legacy_end" -v replacement="$rendered" '
    $0 == begin || $0 == old_begin {
      while ((getline line < replacement) > 0) print line
      close(replacement)
      replacing = 1
      next
    }
    ($0 == end || $0 == old_end) && replacing {
      replacing = 0
      next
    }
    !replacing { print }
  ' "$input_file" >"$updated"
else
  awk -v replacement="$rendered" '
    !inserted && /^# / {
      print
      print ""
      while ((getline line < replacement) > 0) print line
      close(replacement)
      inserted = 1
      next
    }
    { print }
    END { if (!inserted) exit 1 }
  ' "$input_file" >"$updated"
fi

if $check_only; then
  if [[ ! -f "$agents_file" ]] || ! cmp -s "$updated" "$agents_file"; then
    printf 'AGENTS.md 共享入口缺失或偏离模板\n' >&2
    exit 1
  fi
  exit 0
fi
chmod "$agents_mode" "$updated"
mv "$updated" "$agents_file"
