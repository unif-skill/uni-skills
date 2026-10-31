#!/usr/bin/env python3
"""按组织模板核对、补齐单个仓库设置；不配置组织共用凭据。"""

import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent


def read_organization(target, repository=None):
    command = ["node", str(ROOT / "templates/scripts/organization.cjs"), str(target)]
    if repository is not None:
        command.append(repository)
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as error:
        raise RuntimeError("读取工程组织配置需要 Node.js。") from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "工程组织配置校验失败。")
    return json.loads(result.stdout)


def read_required_checks(target, repository):
    root = Path(target).resolve()
    for relative in (".github", ".github/delivery.json"):
        if (root / relative).is_symlink():
            raise RuntimeError("delivery.json 路径不允许 symlink。")
    file = root / ".github/delivery.json"
    if not file.exists():
        return None
    try:
        receipt = json.loads(file.read_text())
    except (OSError, ValueError) as error:
        raise RuntimeError("无法读取 delivery.json。") from error
    if not isinstance(receipt, dict) or type(receipt.get("schemaVersion")) is not int or receipt["schemaVersion"] != 1 \
            or receipt.get("standard") != "github-delivery/react-native" \
            or str(receipt.get("repository", "")).lower() != repository.lower():
        raise RuntimeError("delivery.json 身份或格式与目标 repository 不符。")
    checks = receipt.get("requiredChecks")
    if not isinstance(checks, list) or not checks or not all(
        isinstance(name, str) and name.strip() == name and name and not re.search(r"[\x00-\x1f]", name)
        for name in checks
    ) or len(set(checks)) != len(checks):
        raise RuntimeError("delivery.json requiredChecks 必须是非空、唯一的检查名称数组。")
    return checks


def api(endpoint, method="GET", body=None, missing_ok=False):
    command = ["gh", "api", "--method", method, endpoint]
    if body is not None:
        command.extend(["--input", "-"])
    result = subprocess.run(
        command, input=json.dumps(body) if body is not None else None,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        if missing_ok and "(HTTP 404)" in result.stderr:
            return None
        raise RuntimeError(f"{method} {endpoint}: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def pages(endpoint, key=None):
    page = 1
    while True:
        separator = "&" if "?" in endpoint else "?"
        result = api(f"{endpoint}{separator}per_page=100&page={page}")
        items = result[key] if key else result
        yield from items
        if len(items) < 100:
            return
        page += 1


def differences(current, expected):
    result = {}
    for key, value in expected.items():
        actual = current.get(key)
        if isinstance(value, dict):
            nested = differences(actual if isinstance(actual, dict) else {}, value)
            if nested:
                result[key] = nested
        elif actual != value:
            result[key] = value
    return result


def matches(current, expected):
    if isinstance(expected, dict):
        return isinstance(current, dict) and all(
            key in current and matches(current[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(current, list) and len(current) == len(expected) and all(
            any(matches(item, wanted) for item in current) for wanted in expected
        )
    return current == expected


def desired_rules(template, current, release_app_id=None):
    desired = copy.deepcopy(template)
    actors = copy.deepcopy(current.get("bypass_actors", []) if current else [])
    if release_app_id is not None:
        existing = next((actor for actor in actors
                         if actor.get("actor_type") == "Integration" and actor.get("actor_id") == release_app_id), None)
        if existing is None:
            actors.append({"actor_id": release_app_id, "actor_type": "Integration", "bypass_mode": "always"})
        elif existing.get("bypass_mode") != "always":
            raise RuntimeError("指定发布 App 的既有 bypass 不允许直接推送；请先核对该身份及保护规则。")
    if not any(actor.get("actor_type") == "Integration" and actor.get("bypass_mode") == "always"
               and isinstance(actor.get("actor_id"), int) and actor["actor_id"] > 0 for actor in actors):
        raise RuntimeError("缺少可直接推送的发布 App；请通过 --release-app-id 指定本项目已授权的发布 App ID。")
    desired["bypass_actors"] = actors
    if current is None:
        return desired
    rules = {rule["type"]: copy.deepcopy(rule) for rule in current["rules"]}
    for rule in template["rules"]:
        kind = rule["type"]
        existing = rules.get(kind, {})
        parameters = {**rule.get("parameters", {}), **existing.get("parameters", {})}
        if kind == "required_status_checks":
            parameters["strict_required_status_checks_policy"] = bool(
                existing.get("parameters", {}).get("strict_required_status_checks_policy")
                or rule.get("parameters", {}).get("strict_required_status_checks_policy")
            )
            checks = {
                check["context"]: check
                for check in existing.get("parameters", {}).get("required_status_checks", [])
            }
            for check in rule["parameters"]["required_status_checks"]:
                checks[check["context"]] = {**checks.get(check["context"], {}), **check}
            parameters["required_status_checks"] = list(checks.values())
        rules[kind] = {"type": kind, **({"parameters": parameters} if parameters else {})}
    desired["rules"] = list(rules.values())
    return desired


def assert_registered_checks(base, branch, required, native):
    registered = set()
    workflows = ["ci.yml"] + (["native-lint.yml"] if native else [])
    for workflow in workflows:
        runs = api(f"{base}/actions/workflows/{workflow}/runs?branch={quote(branch, safe='')}&per_page=5")
        for run in runs["workflow_runs"]:
            registered.update(job["name"] for job in pages(f"{base}/actions/runs/{run['id']}/jobs", "jobs"))
            if required <= registered:
                return
    raise RuntimeError("CI 尚未注册全部必需检查，未修改远端：" + ", ".join(sorted(required - registered)))


def plan(repository, release_app_id=None, organization=None, required_checks=None):
    organization = organization or {}
    base = f"repos/{repository}"
    repo = api(base)
    if not repo.get("permissions", {}).get("admin"):
        raise RuntimeError("需要该仓库的管理员权限才能完整核对和配置远端设置。")
    native = api(f"{base}/contents/.github/workflows/native-lint.yml", missing_ok=True) is not None
    template_name = "protect-main-native.json" if native else "protect-main.json"
    template = json.loads((ROOT / "scripts/rulesets" / template_name).read_text())
    if required_checks is not None:
        for rule in template["rules"]:
            if rule["type"] == "required_status_checks":
                rule["parameters"]["required_status_checks"] = [{"context": name} for name in required_checks]
    required = {
        check["context"] for rule in template["rules"]
        if rule["type"] == "required_status_checks"
        for check in rule["parameters"]["required_status_checks"]
    }
    assert_registered_checks(base, repo["default_branch"], required, native)

    changes = []
    desired = organization.get("repositorySettings", {})
    patch = differences(repo, desired)
    if patch:
        changes.append(("仓库合并选项／安全开关", "PATCH", base, patch))

    owned = [rule for rule in pages(f"{base}/rulesets?includes_parents=false") if rule["name"] == template["name"]]
    if len(owned) > 1:
        raise RuntimeError("存在多个同名 protect main 规则，请先明确保留对象。")
    current = api(f"{base}/rulesets/{owned[0]['id']}") if owned else None
    rules = desired_rules(template, current, release_app_id)
    if current is None:
        changes.append(("主分支保护", "POST", f"{base}/rulesets", rules))
    elif not matches(current, rules):
        changes.append(("主分支保护", "PUT", f"{base}/rulesets/{current['id']}", rules))

    security = organization.get("security", {})
    if "privateVulnerabilityReporting" in security:
        reporting = api(f"{base}/private-vulnerability-reporting")
        if type(reporting.get("enabled")) is not bool:
            raise RuntimeError("未取得私密漏洞报告状态。")
        expected = security["privateVulnerabilityReporting"]
        if reporting["enabled"] != expected:
            changes.append(("私密漏洞报告", "PUT" if expected else "DELETE", f"{base}/private-vulnerability-reporting", None))
    if "dependabotSecurityUpdates" in security:
        security_updates = repo.get("security_and_analysis", {}).get("dependabot_security_updates", {}).get("status")
        if security_updates not in ("enabled", "disabled"):
            raise RuntimeError("未取得自动安全更新状态，不能将缺失信息视为已关闭。")
        expected = security["dependabotSecurityUpdates"]
        if security_updates != expected:
            changes.append(("自动安全更新 PR", "PUT" if expected == "enabled" else "DELETE", f"{base}/automated-security-fixes", None))
    if "codeqlDefaultSetup" in security:
        codeql = api(f"{base}/code-scanning/default-setup")
        if codeql.get("state") not in ("configured", "not-configured"):
            raise RuntimeError("未取得 CodeQL 默认设置状态。")
        expected = security["codeqlDefaultSetup"]
        if codeql["state"] != expected:
            changes.append(("CodeQL 默认设置", "PATCH", f"{base}/code-scanning/default-setup", {"state": expected}))

    website = api(f"{base}/contents/.github/workflows/deploy-docs.yml", missing_ok=True)
    if website is not None:
        site = api(f"{base}/pages", missing_ok=True)
        if site is None:
            changes.append(("Pages 与网站入口", "POST", f"{base}/pages", {"build_type": "workflow"}))
        else:
            expected_url = organization.get("pagesURL", "").replace("{repo}", repository.split("/")[1])
            if expected_url and site.get("html_url", "").rstrip("/") != expected_url.rstrip("/"):
                raise RuntimeError("远端 Pages 地址与工程 pagesURL 不符，未修改远端。")
            if site["build_type"] != "workflow":
                changes.append(("Pages 构建方式", "PUT", f"{base}/pages", {"build_type": "workflow"}))
            if repo.get("homepage") != site["html_url"]:
                changes.append(("网站入口", "PATCH", base, {"homepage": site["html_url"]}))
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="明确的 GitHub owner/repo")
    parser.add_argument("--check", action="store_true", help="只读核验；有差异或前置缺失时返回非零")
    parser.add_argument("--release-app-id", type=int, help="本项目已授权的发布 App ID；保留其他既有 bypass actors")
    parser.add_argument("--target-path", default=".", help="目标工程路径，缺省为当前目录")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9_.-]+", args.repository) \
            or args.repository.split("/")[-1] in (".", ".."):
        parser.error("只接受明确的 owner/repo，不接受 URL 或本地路径。")
    if args.release_app_id is not None and args.release_app_id <= 0:
        parser.error("--release-app-id 必须是正整数。")
    organization = read_organization(args.target_path, args.repository) or {}
    configured_app = organization.get("releaseAppId")
    if configured_app is not None and args.release_app_id is not None and configured_app != args.release_app_id:
        raise RuntimeError("--release-app-id 与工程 releaseAppId 不符，未访问远端。")
    release_app_id = configured_app if configured_app is not None else args.release_app_id
    required_checks = read_required_checks(args.target_path, args.repository)
    changes = plan(args.repository, release_app_id, organization, required_checks)
    if args.check:
        for label, _, _, _ in changes:
            print(f"需补齐：{label}")
        if changes:
            return 1
    else:
        for label, method, endpoint, body in changes:
            print(f"配置：{label}", flush=True)
            api(endpoint, method, body)
            if method == "POST" and endpoint.endswith("/pages"):
                site = api(endpoint)
                api(f"repos/{args.repository}", "PATCH", {"homepage": site["html_url"]})
        remaining = plan(args.repository, release_app_id, organization, required_checks) if changes else []
        if remaining:
            raise RuntimeError("配置后回读仍有差异：" + ", ".join(item[0] for item in remaining))
    print(f"通过：{args.repository} 远端仓库设置与主分支规则符合模板。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"失败：{error}", file=sys.stderr)
        sys.exit(1)
