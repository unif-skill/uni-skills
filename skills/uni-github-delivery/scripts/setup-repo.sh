#!/usr/bin/env bash
# 按已采用模板配置 owner/repo；已有设置跳过，--check 只读核验。
# 先同步并运行 CI，确保模板要求的检查已经注册。
# 新发布身份仅通过明确的 --release-app-id 提供，不创建 App 或配置密钥。
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/setup_repo.py" "$@"
