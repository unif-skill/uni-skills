#!/usr/bin/env bash
# 把 uni-github-delivery 的 templates/ 同步到目标 repo 工作树。
#
# 跟 setup-repo.sh 分工:
#   - setup-repo.sh —— 按工程采用记录与组织配置核对、调整 GitHub 仓库设置和规则,走 gh api
#   - sync-repo.sh  —— 下发 repo 内的 workflow + 配置文件(本脚本),走文件拷贝 + 变量替换
#
# 用法:
#   bash scripts/sync-repo.sh [--check] [--pr-agent] <owner/repo> [target-repo-path]
#     <owner/repo>        目标 repo 名(如 example/widget),用于 {{REPO}} / URL 替换
#     [target-repo-path] 目标 repo 本地工作树路径,默认当前目录
#
# 行为:
#   - 只改目标 repo 的【工作树】,不 git add / commit / push —— 改动留给你 review,各仓自己提 PR。
#   - 幂等:可反复跑。
#   - --check 只读核对;--pr-agent 仅用于项目已明确选择的 PR Agent 接入。
#
# 覆盖策略(关键):
#   - 更新受管文件;采用记录 projectFiles 中已声明的项目专用工作流保留,仍核对摘要:
#       .github/workflows/{ci,release,pr-title}.yml;PR Agent 工作流按项目采用情况选择
#       .github/actions/setup/action.yml
#       lefthook.yml
#       .github/ISSUE_TEMPLATE/{bug_report,config}.yml
#   - 仅移除目标工程 .github/organization.json 的 obsoleteFiles 明确列出的停用自动化。
#   - marker 级覆盖(共享 Agent bootstrap,保留仓库特有规则):
#       AGENTS.md 内的 GITHUB DELIVERY STANDARD 区块;已有旧标识按同步工具迁移
#   - 仅当目标【不存在】时创建(保留各仓 repo 特化,不覆盖):
#       SECURITY.md / .github/PULL_REQUEST_TEMPLATE.md(保留项目政策与 checklist)
#       .pr_agent.toml(各仓有特化 review 规则)
#       .github/ISSUE_TEMPLATE/feature_request.yml(各仓有特化字段)
#   - 条件分发:
#       deploy-docs.yml 仅当目标有 website/ 目录
#       native-lint.yml + nightly-build-check.yml + .clang-format 仅当目标有手写 native 源码(.kt/.mm)
#   - release.yml 的 on.push.paths:目标有 *.podspec → native paths,否则 JS-only paths
#
# 变量替换:
#   {{REPO}}      → repo 名
#   {{NPM_PKG}}   → npm 包名(从目标 package.json 的 "name" 读;缺失时失败)
#   {{PAGES_URL}} → https://<owner>.github.io/<repo>/

set -euo pipefail

# ── 参数 ──────────────────────────────────────────────────────────────
CHECK_ONLY=false
PR_AGENT=false
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --check) CHECK_ONLY=true ;;
    --pr-agent) PR_AGENT=true ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
  shift
done
DIFFERENCES=0
REPOSITORY="${1:-}"
[[ "$REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo "需要 owner/repo" >&2; exit 2; }
OWNER="${REPOSITORY%%/*}"
REPO="${REPOSITORY#*/}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/templates"

if [[ -z "$REPO" ]]; then
  echo "用法: $0 [--check] <owner/repo> [target-repo-path]"
  echo "  例: $0 example/widget /path/to/widget"
  exit 1
fi

TARGET="${2:-$PWD}"
TARGET="$(cd "$TARGET" && pwd)"

if [[ ! -d "$TARGET" ]]; then
  echo "✗ 目标 repo 路径不存在: $TARGET"
  echo "  传第二参数指定路径,并确保目录存在。"
  exit 1
fi
if [[ ! -d "$TEMPLATES_DIR" ]]; then
  echo "✗ templates 目录不存在: $TEMPLATES_DIR"
  exit 1
fi

# ── 解析变量 ──────────────────────────────────────────────────────────
# NPM_PKG:优先从目标 package.json 的 "name" 字段读真实包名
NPM_PKG=""
if [[ -f "$TARGET/package.json" ]]; then
  NPM_PKG="$(node -e 'try{process.stdout.write(require(process.argv[1]).name||"")}catch(e){}' "$TARGET/package.json" 2>/dev/null || true)"
fi
if [[ -z "$NPM_PKG" ]]; then
  echo "目标 package.json 必须声明真实包名" >&2
  exit 1
fi
PAGES_URL="$(node -e 'const fs=require("fs"); const lib=require(process.argv[1]); const p=JSON.parse(fs.readFileSync(process.argv[2]+"/package.json")); const c=lib.readOrganization(process.argv[2],process.argv[3]); lib.validateIdentity(c,p,process.argv[3]); process.stdout.write(lib.resolvePagesURL(c,process.argv[3]) || p.homepage || "https://"+process.argv[4]+".github.io/"+process.argv[5]+"/")' "$TEMPLATES_DIR/scripts/organization.cjs" "$TARGET" "$REPOSITORY" "$OWNER" "$REPO")"

# 目标是否为 native 仓(有 *.podspec) / 是否有 website
HAS_PODSPEC=false
if ls "$TARGET"/*.podspec >/dev/null 2>&1; then HAS_PODSPEC=true; fi
HAS_WEBSITE=false
if [[ -d "$TARGET/website" ]]; then HAS_WEBSITE=true; fi

# 是否有「手写 native 源码」—— 决定 native-lint.yml / .clang-format / nightly-build-check.yml 下不下发。
# 只看库本体的 android/src + ios/(crnl 布局下 example app 的 native 在 example/ 下,不会误命中)。
# 判据用源码而非 *.podspec:design 纯 JS 但可能有壳 podspec,而 native lint 只对真有 .kt/.mm 的仓有意义。
HAS_NATIVE_SRC="$(node -e 'process.stdout.write(String(require(process.argv[1]).features(process.argv[2]).native))' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET")"

echo "→ 同步 templates → $REPO"
echo "  target     : $TARGET"
echo "  npm pkg    : $NPM_PKG"
echo "  pages url  : $PAGES_URL"
echo "  podspec    : $HAS_PODSPEC"
echo "  native src : $HAS_NATIVE_SRC (有 .kt/.mm → 下发 native-lint + .clang-format + nightly)"
echo "  website    : $HAS_WEBSITE"
echo ""

RENDER_DIR="$(mktemp -d)"
trap 'rm -rf "$RENDER_DIR"' EXIT
MANAGED_FILES="$RENDER_DIR/managed-files"
PROJECT_FILES="$RENDER_DIR/project-files"
: > "$MANAGED_FILES"
node -e 'const fs=require("fs"); const {projectFiles}=require(process.argv[2]); const p=process.argv[1]; if(fs.existsSync(p)) for(const f of projectFiles(JSON.parse(fs.readFileSync(p)).projectFiles)) console.log(f)' "$TARGET/.github/delivery.json" "$TEMPLATES_DIR/scripts/check-delivery.cjs" > "$PROJECT_FILES"
if [[ -f "$TARGET/.github/organization.json" ]]; then printf '%s\n' .github/organization.json >> "$MANAGED_FILES"; fi

# ── 工具函数 ──────────────────────────────────────────────────────────
# 变量替换:stdin → stdout
subst() {
  node -e 'const fs=require("fs"); let text=fs.readFileSync(0,"utf8"); ["OWNER","REPO","NPM_PKG","PAGES_URL"].forEach((key,i)=>{text=text.replaceAll("{{"+key+"}}",process.argv[i+1]);}); process.stdout.write(text)' "$OWNER" "$REPO" "$NPM_PKG" "$PAGES_URL"
}

# 强制写(替换变量后覆盖目标)
# render <template-rel-path> <target-rel-path>
write_rendered() {
  local src="$1"
  local dst="$TARGET/$2"
  node -e 'require(process.argv[1]).inside(process.argv[2],process.argv[3])' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET" "$2"
  printf '%s\n' "$2" >> "$MANAGED_FILES"
  if grep -Fxq "$2" "$PROJECT_FILES"; then return; fi
  if $CHECK_ONLY; then
    if [[ ! -f "$dst" ]] || ! cmp -s "$src" "$dst"; then
      echo "  ✗ $2(缺失或偏离组织模板)"
      DIFFERENCES=$((DIFFERENCES + 1))
    fi
    return
  fi
  if [[ -L "$dst" ]]; then
    echo "拒绝覆盖符号链接: $2" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dst")"
  cat "$src" > "$dst"
  echo "  ✓ $2"
}

render() {
  subst < "$TEMPLATES_DIR/$1" > "$RENDER_DIR/rendered"
  write_rendered "$RENDER_DIR/rendered" "$2"
}

# 仅当目标不存在时写(保留 repo 特化)
# render_if_absent <template-rel-path> <target-rel-path>
render_if_absent() {
  local dst="$TARGET/$2"
  node -e 'require(process.argv[1]).inside(process.argv[2],process.argv[3])' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET" "$2"
  if [[ -e "$dst" ]]; then
    echo "  ⊘ $2(已存在,保留 repo 特化,跳过)"
    return
  fi
  if $CHECK_ONLY; then
    echo "  ✗ $2(缺失)"
    DIFFERENCES=$((DIFFERENCES + 1))
    return
  fi
  mkdir -p "$(dirname "$dst")"
  subst < "$TEMPLATES_DIR/$1" > "$dst"
}

# 删除不再使用的受管文件(同时兼容清理历史旧名)。
# prune_stale <target-rel-path>
prune_stale() {
  local dst="$TARGET/$1"
  node -e 'require(process.argv[1]).inside(process.argv[2],process.argv[3])' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET" "$1"
  if [[ -e "$dst" ]]; then
    if $CHECK_ONLY; then
      echo "  ✗ $1(已停用，需移除)"
      DIFFERENCES=$((DIFFERENCES + 1))
      return
    fi
    if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 && \
       git -C "$TARGET" ls-files --error-unmatch "$1" >/dev/null 2>&1; then
      rm -f "$dst"   # 仅修改工作树，由采用工程提交
    else
      rm -f "$dst"
    fi
    echo "  ✗ $1(旧名文件,已删除)"
  fi
}

# 仅清理项目已明确采用的停用配置。
node -e 'const {readOrganization}=require(process.argv[1]); for(const file of readOrganization(process.argv[2],process.argv[3])?.obsoleteFiles || []) console.log(file)' "$TEMPLATES_DIR/scripts/organization.cjs" "$TARGET" "$REPOSITORY" > "$RENDER_DIR/obsolete"
while IFS= read -r obsolete; do
  prune_stale "$obsolete"
done < "$RENDER_DIR/obsolete"

# ── 1. 强制覆盖的 workflow / 配置文件 ────────────────────────────────
echo "→ [1] 强制覆盖(统一标准)"
render workflows/ci.yml                       .github/workflows/ci.yml
render actions/setup/action.yml              .github/actions/setup/action.yml
render actions/changes/action.yml            .github/actions/changes/action.yml
render actions/changes/classify-package.cjs    .github/actions/changes/classify-package.cjs
if grep -q "actions/verification" "$TARGET/.github/workflows/ci.yml"; then
  render actions/verification/verification.cjs   .github/actions/verification/verification.cjs
  render actions/verification/verification.test.cjs .github/actions/verification/verification.test.cjs
fi
render scripts/check-library.cjs             .github/scripts/check-library.cjs
render scripts/check-delivery.cjs            .github/scripts/check-delivery.cjs
render scripts/organization.cjs              .github/scripts/organization.cjs
render workflows/pr-title.yml                 .github/workflows/pr-title.yml
if $PR_AGENT || [[ -f "$TARGET/.github/workflows/pr-agent.yml" ]]; then
  render workflows/pr-agent.yml .github/workflows/pr-agent.yml
  render workflows/pr-agent-reusable.yml .github/workflows/pr-agent-reusable.yml
fi
render lefthook.yml                           lefthook.yml
render_if_absent SECURITY.md                  SECURITY.md
render ISSUE_TEMPLATE/bug_report.yml          .github/ISSUE_TEMPLATE/bug_report.yml
render ISSUE_TEMPLATE/config.yml              .github/ISSUE_TEMPLATE/config.yml
echo ""

# ── 1b. 共享 Agent bootstrap(marker 级覆盖,保留仓库规则)──────────────
echo "→ [1b] 同步共享 Agent bootstrap(marker 级覆盖)"
if [[ -f "$TARGET/package.json" ]]; then
  if $CHECK_ONLY; then
    if ! bash "$SCRIPT_DIR/sync-agent-standards.sh" --check "$REPO" "$TARGET"; then
      DIFFERENCES=$((DIFFERENCES + 1))
    fi
    if $HAS_WEBSITE && ! node "$SCRIPT_DIR/sync-llms.cjs" --check "$REPO" "$TARGET"; then
      DIFFERENCES=$((DIFFERENCES + 1))
    fi
  else
    bash "$SCRIPT_DIR/sync-agent-standards.sh" "$REPO" "$TARGET"
    if $HAS_WEBSITE; then node "$SCRIPT_DIR/sync-llms.cjs" "$REPO" "$TARGET"; fi
    echo "  ✓ AGENTS.md 共享入口(保留仓库特有规则)"
  fi
else
  echo "  ⊘ 非共享 Agent 标准目标仓,跳过 AGENTS.md"
fi
echo ""

# ── 2. release.yml(按 native/JS 决定 paths)────────────────────────
if $HAS_WEBSITE; then node "$SCRIPT_DIR/sync-llms.cjs" --list-managed "$REPO" "$TARGET" >> "$MANAGED_FILES"; fi
echo "→ [2] release.yml(按 native/JS 注入 paths)"
# 把多行 paths 写进临时文件,再让 awk 命中 {{RELEASE_PATHS}} 时 cat 进来
# —— 不经 awk -v 传多行串(BSD awk 会报 "newline in string")。
PATHS_TMP="$RENDER_DIR/release-paths"
if $HAS_PODSPEC; then
  printf "%s\n" \
    "      - 'src/**'" \
    "      - 'ios/**'" \
    "      - 'android/**'" \
    "      - '*.podspec'" > "$PATHS_TMP"
else
  printf "%s\n" \
    "      - 'src/**'" \
    "      - 'scripts/**'" > "$PATHS_TMP"
fi
subst < "$TEMPLATES_DIR/workflows/release.yml" \
  | awk -v pf="$PATHS_TMP" '
      # 只替换首个 {{RELEASE_PATHS}} 标记行(防 header 注释里再次出现导致重复注入)
      !done && index($0, "{{RELEASE_PATHS}}") {
        while ((getline line < pf) > 0) print line
        close(pf)
        done = 1
        next
      }
      { print }
    ' > "$RENDER_DIR/release.yml"
write_rendered "$RENDER_DIR/release.yml" .github/workflows/release.yml
echo ""

# ── 3. deploy-docs.yml(仅有 website 的仓)────────────────────────────
echo "→ [3] deploy-docs.yml(条件分发)"
if $HAS_WEBSITE; then
  render workflows/deploy-docs.yml            .github/workflows/deploy-docs.yml
else
  echo "  ⊘ 目标无 website/,跳过 deploy-docs.yml"
fi
echo ""

# ── 3b. native lint / nightly(仅有手写 native 源码的仓)────────────────
echo "→ [3b] native lint / nightly build-check(条件分发)"
HAS_NATIVE_CHECKS="$(node -e 'const fs=require("fs");const p=process.argv[1];const checks=fs.existsSync(p)?JSON.parse(fs.readFileSync(p)).requiredChecks:null;process.stdout.write(String(checks?checks.some(name=>["lint-cpp","lint-kotlin"].includes(name)):process.argv[2]==="true"))' "$TARGET/.github/delivery.json" "$HAS_NATIVE_SRC")"
if $HAS_NATIVE_CHECKS; then
  # native-lint.yml 是 required check —— 配套的 lint-cpp/lint-kotlin 会被 setup-repo.sh
  # 自动加进 8-check ruleset。.clang-format 放仓库根,clang-format 自动发现。
  render workflows/native-lint.yml            .github/workflows/native-lint.yml
  render workflows/nightly-build-check.yml    .github/workflows/nightly-build-check.yml
  render .clang-format                        .clang-format
else
  echo "  ⊘ 目标无 native 源码(.kt/.mm),跳过 native-lint / nightly / .clang-format"
fi
echo ""

# ── 4. 仅缺时创建(保留 repo 特化)───────────────────────────────────
echo "→ [4] 仅当不存在时创建(保留 repo 特化)"
render_if_absent PULL_REQUEST_TEMPLATE.md          .github/PULL_REQUEST_TEMPLATE.md
render_if_absent pr_agent.toml                     .pr_agent.toml
render_if_absent ISSUE_TEMPLATE/feature_request.yml .github/ISSUE_TEMPLATE/feature_request.yml
echo ""

# ── 4b. 校验 workflow 依赖；缺失时非零退出，不修改 package.json ──
# workflow 文件同步过去了,但它运行时依赖 package.json 里的配置 —— 那些是各仓特化、sync 故意不碰:
#   ci.yml / nightly 的 `yarn turbo run build:*`      → devDep turbo
#   release.yml 的 `npx release-it`(npm OIDC publish) → release-it 配置 + npm.skipChecks + conventional-changelog plugin
# 同步时校验这些运行依赖,缺失则报告失败,不改写项目 package.json。
echo "→ [4b] 校验 package.json 的 workflow 依赖配置"
if ! node -e 'const fs=require("fs"); const {dependencies}=require(process.argv[1]); dependencies(JSON.parse(fs.readFileSync(process.argv[2])))' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET/package.json"; then
  DIFFERENCES=$((DIFFERENCES + 1))
fi
echo ""

if $CHECK_ONLY; then
  if ! node -e 'require(process.argv[1]).checkDelivery(process.argv[2])' "$TEMPLATES_DIR/scripts/check-delivery.cjs" "$TARGET"; then
    DIFFERENCES=$((DIFFERENCES + 1))
  fi
  if [[ "$DIFFERENCES" -gt 0 ]]; then
    echo "模板核验失败：$DIFFERENCES 项差异；未修改目标仓库。"
    exit 1
  fi
  echo "模板与工作流依赖配置一致；未修改目标仓库。"
  exit 0
fi
if [[ "$DIFFERENCES" -gt 0 ]]; then
  echo "文件已同步，但接入配置仍有缺项，不能报告接入完成。"
  exit 1
fi

node "$SCRIPT_DIR/write-delivery.cjs" "$TARGET" "$MANAGED_FILES" "$REPOSITORY"

# ── 5. 报告 diff(不 commit 不 push)─────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 仓库文件同步完成(未 commit / 未 push；未核验 GitHub 远端设置)。改动:"
echo ""
if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$TARGET" status --short
  echo ""
  git -C "$TARGET" diff --stat
else
  echo "  (目标不是 git 仓库,无法显示 diff)"
fi
echo ""
echo "下一步:在 $TARGET 里 review 改动,自己 commit + 开 PR。"

echo "CI 检查注册后，核验远端模板: $SCRIPT_DIR/setup-repo.sh $REPOSITORY --check"
echo "仅在已获远端配置授权时补齐差异: $SCRIPT_DIR/setup-repo.sh $REPOSITORY"
