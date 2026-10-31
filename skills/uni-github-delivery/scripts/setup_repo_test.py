import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("setup_repo", ROOT / "scripts/setup_repo.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
REPOSITORY = "example-org/contract-fixture"
BASE = f"repos/{REPOSITORY}"
RELEASE_ACTOR = {"actor_id": 12345, "actor_type": "Integration", "bypass_mode": "always"}
TEMPLATE = json.loads((ROOT / "scripts/rulesets/protect-main.json").read_text())
SETTINGS = json.loads((ROOT / "templates/repository-settings.json").read_text())
CHECKS = ["actionlint", "lint", "test", "build-library", "build-android", "build-ios", "verified"]
PROFILE = {
    "schemaVersion": 1, "owner": "example-org", "releaseAppId": 12345,
    "pagesURL": "https://example-org.github.io/{repo}/",
    "repositorySettings": SETTINGS,
    "security": {"codeqlDefaultSetup": "not-configured", "dependabotSecurityUpdates": "disabled",
                 "privateVulnerabilityReporting": True},
}


class GithubFixture:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="delivery-setup-")
        self.target = Path(self.temporary.name)
        (self.target / ".github").mkdir()
        self.profile = copy.deepcopy(PROFILE)
        self.save_profile()
        self.repo = copy.deepcopy(SETTINGS)
        self.repo.update(default_branch="main", permissions={"admin": True}, homepage=None)
        self.repo["security_and_analysis"]["dependabot_security_updates"] = {"status": "disabled"}
        self.ruleset = {**copy.deepcopy(TEMPLATE), "id": 1, "bypass_actors": [copy.deepcopy(RELEASE_ACTOR)]}
        self.reporting = True
        self.codeql = "not-configured"
        self.checks = list(CHECKS)
        self.native = False
        self.native_checks = []
        self.website = False
        self.site = None
        self.ignore_writes = False
        self.calls = []

    def save_profile(self):
        (self.target / ".github/organization.json").write_text(json.dumps(self.profile))

    def save_delivery(self, checks):
        (self.target / ".github/delivery.json").write_text(json.dumps({
            "schemaVersion": 1, "standard": "uni-github-delivery/rn", "repository": REPOSITORY,
            "requiredChecks": checks,
        }))

    @property
    def writes(self):
        return [call for call in self.calls if call[1] != "GET"]

    def api(self, endpoint, method="GET", body=None, missing_ok=False):
        self.calls.append((endpoint, method, copy.deepcopy(body)))
        if method != "GET":
            if self.ignore_writes:
                return None
            if endpoint == BASE:
                for key, value in body.items():
                    if isinstance(value, dict):
                        self.repo[key].update(copy.deepcopy(value))
                    else:
                        self.repo[key] = value
            elif "/rulesets" in endpoint:
                self.ruleset = {**copy.deepcopy(body), "id": 1}
            elif endpoint.endswith("/private-vulnerability-reporting"):
                self.reporting = method == "PUT"
            elif endpoint.endswith("/automated-security-fixes"):
                self.repo["security_and_analysis"]["dependabot_security_updates"]["status"] = "enabled" if method == "PUT" else "disabled"
            elif endpoint.endswith("/code-scanning/default-setup"):
                self.codeql = body["state"]
            elif endpoint.endswith("/pages"):
                self.site = {"html_url": "https://example-org.github.io/contract-fixture/", **body}
            else:
                raise AssertionError((endpoint, method, body))
            return None
        if endpoint == BASE:
            return copy.deepcopy(self.repo)
        if "/contents/.github/workflows/" in endpoint:
            if endpoint.endswith("deploy-docs.yml") and self.website:
                return {"type": "file"}
            if endpoint.endswith("native-lint.yml") and self.native:
                return {"type": "file"}
            assert missing_ok
            return None
        if "/actions/workflows/ci.yml/runs?" in endpoint:
            return {"workflow_runs": [{"id": 10}]}
        if "/actions/workflows/native-lint.yml/runs?" in endpoint:
            return {"workflow_runs": [{"id": 20}]}
        if "/actions/runs/10/jobs?" in endpoint:
            offset = 100 if endpoint.endswith("page=2") else 0
            return {"jobs": [{"name": name} for name in self.checks[offset:offset + 100]]}
        if "/actions/runs/20/jobs?" in endpoint:
            return {"jobs": [{"name": name} for name in self.native_checks]}
        if endpoint.startswith(BASE + "/rulesets?"):
            return [] if self.ruleset is None else [{"id": 1, "name": "protect main"}]
        if endpoint == BASE + "/rulesets/1":
            return copy.deepcopy(self.ruleset)
        if endpoint.endswith("/private-vulnerability-reporting"):
            return {"enabled": self.reporting}
        if endpoint.endswith("/code-scanning/default-setup"):
            return {"state": self.codeql}
        if endpoint.endswith("/pages"):
            assert missing_ok or self.site is not None
            return copy.deepcopy(self.site)
        raise AssertionError(endpoint)


class SetupTests(unittest.TestCase):
    def run_setup(self, fixture, *args, repository=REPOSITORY):
        self.addCleanup(fixture.temporary.cleanup)
        with patch.object(setup, "api", fixture.api), patch.object(sys, "argv", ["setup-repo", repository, "--target-path", str(fixture.target), *args]), contextlib.redirect_stdout(io.StringIO()):
            return setup.main()

    def test_profile_conflicts_stop_before_api_calls(self):
        fixture = GithubFixture()
        fixture.profile["owner"] = "another-org"
        fixture.save_profile()
        with self.assertRaisesRegex(RuntimeError, "owner"):
            self.run_setup(fixture)
        self.assertEqual(fixture.calls, [])
        fixture.profile["owner"] = "example-org"
        fixture.save_profile()
        with self.assertRaisesRegex(RuntimeError, "releaseAppId"):
            self.run_setup(fixture, "--release-app-id", "67890")
        self.assertEqual(fixture.calls, [])

    def test_omitted_organization_policies_preserve_remote_settings_and_security(self):
        for present in [False, True]:
            fixture = GithubFixture()
            fixture.profile = {"schemaVersion": 1, "owner": "example-org"}
            fixture.save_profile()
            if not present:
                (fixture.target / ".github/organization.json").unlink()
            fixture.repo["allow_merge_commit"] = True
            fixture.repo["security_and_analysis"]["dependabot_security_updates"]["status"] = "enabled"
            fixture.reporting = False
            fixture.codeql = "configured"
            self.assertEqual(self.run_setup(fixture), 0)
            self.assertEqual(fixture.writes, [])
            self.assertFalse(any(call[0].endswith(("/private-vulnerability-reporting", "/code-scanning/default-setup")) for call in fixture.calls))

    def test_profile_release_identity_cannot_be_replaced_by_an_unrelated_app(self):
        fixture = GithubFixture()
        fixture.ruleset["bypass_actors"][0]["actor_id"] = 67890
        self.assertEqual(self.run_setup(fixture, "--check"), 1)
        self.assertEqual(fixture.writes, [])
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.ruleset["bypass_actors"], [
            {"actor_id": 67890, "actor_type": "Integration", "bypass_mode": "always"}, RELEASE_ACTOR,
        ])

    def test_adopted_legacy_ci_checks_remain_unchanged_and_preserve_remote_extras(self):
        for native in [False, True]:
            fixture = GithubFixture()
            fixture.native = native
            fixture.checks.remove("verified")
            fixture.native_checks = ["lint-cpp", "lint-kotlin"] if native else []
            adopted = fixture.checks + fixture.native_checks
            fixture.save_delivery(adopted)
            required = [{"context": name} for name in adopted] + [{"context": "custom-check", "integration_id": 987}]
            fixture.ruleset["rules"][3]["parameters"]["required_status_checks"] = required
            self.assertEqual(self.run_setup(fixture, "--check"), 0)
            self.assertEqual(fixture.ruleset["rules"][3]["parameters"]["required_status_checks"], required)
            self.assertEqual(fixture.writes, [])

    def test_invalid_adopted_checks_stop_before_api_calls(self):
        for checks in [[], "actionlint", ["actionlint", "actionlint"], [123], ["line\nbreak"]]:
            fixture = GithubFixture()
            fixture.save_delivery(checks)
            with self.assertRaisesRegex(RuntimeError, "requiredChecks"):
                self.run_setup(fixture)
            self.assertEqual(fixture.calls, [])

    def test_pages_identity_conflict_does_not_change_other_remote_settings(self):
        fixture = GithubFixture()
        fixture.website = True
        fixture.site = {"html_url": "https://wrong.example.org/", "build_type": "workflow"}
        fixture.repo["allow_merge_commit"] = True
        with self.assertRaisesRegex(RuntimeError, "pagesURL"):
            self.run_setup(fixture)
        self.assertEqual(fixture.writes, [])

    def test_explicit_security_policy_can_enable_updates_and_disable_private_reporting(self):
        fixture = GithubFixture()
        fixture.profile["security"] = {"codeqlDefaultSetup": "configured", "dependabotSecurityUpdates": "enabled", "privateVulnerabilityReporting": False}
        fixture.save_profile()
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.repo["security_and_analysis"]["dependabot_security_updates"]["status"], "enabled")
        self.assertEqual(fixture.codeql, "configured")
        self.assertFalse(fixture.reporting)

    def test_explicit_repository_is_used_for_every_remote_request(self):
        fixture = GithubFixture()
        fixture.repo["allow_merge_commit"] = True
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertTrue(fixture.writes)
        self.assertTrue(all(call[0] == BASE or call[0].startswith(BASE + "/") for call in fixture.calls))

    def test_invalid_repository_and_release_identity_stop_before_api_calls(self):
        for repository in ["contract-fixture", "https://github.com/example/repo", "example/../repo", "example/repo?query=1"]:
            fixture = GithubFixture()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.run_setup(fixture, repository=repository)
            self.assertEqual(fixture.calls, [])
        for app_id in ["0", "-1", "not-an-id"]:
            fixture = GithubFixture()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.run_setup(fixture, "--release-app-id", app_id)
            self.assertEqual(fixture.calls, [])

    def test_missing_release_identity_prevents_every_write(self):
        for existing in [None, [], [{"actor_id": 987, "actor_type": "Team", "bypass_mode": "always"}],
                         [{"actor_id": 12345, "actor_type": "Integration", "bypass_mode": "pull_request"}]]:
            fixture = GithubFixture()
            del fixture.profile["releaseAppId"]
            fixture.save_profile()
            if existing is None:
                fixture.ruleset = None
            else:
                fixture.ruleset["bypass_actors"] = existing
            fixture.repo["allow_merge_commit"] = True
            with self.assertRaisesRegex(RuntimeError, "release-app-id|发布.*App"):
                self.run_setup(fixture)
            self.assertEqual(fixture.writes, [])

    def test_existing_bypass_actors_are_preserved_when_updating_rules(self):
        fixture = GithubFixture()
        fixture.ruleset["bypass_actors"].append({"actor_id": 987, "actor_type": "Team", "bypass_mode": "pull_request"})
        expected = copy.deepcopy(fixture.ruleset["bypass_actors"])
        fixture.ruleset["rules"][3]["parameters"]["required_status_checks"].pop()
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.ruleset["bypass_actors"], expected)

    def test_explicit_release_app_is_added_without_replacing_existing_actors(self):
        fixture = GithubFixture()
        del fixture.profile["releaseAppId"]
        fixture.save_profile()
        original = copy.deepcopy(fixture.ruleset["bypass_actors"])
        self.assertEqual(self.run_setup(fixture, "--release-app-id", "67890"), 0)
        self.assertEqual(fixture.ruleset["bypass_actors"], original + [
            {"actor_id": 67890, "actor_type": "Integration", "bypass_mode": "always"},
        ])
        fixture.calls.clear()
        self.assertEqual(self.run_setup(fixture, "--release-app-id", "67890"), 0)
        self.assertEqual(fixture.writes, [])

    def test_explicit_app_does_not_widen_an_existing_restricted_bypass(self):
        fixture = GithubFixture()
        fixture.ruleset["bypass_actors"][0]["bypass_mode"] = "pull_request"
        original = copy.deepcopy(fixture.ruleset)
        with self.assertRaisesRegex(RuntimeError, "既有 bypass"):
            self.run_setup(fixture, "--release-app-id", "12345")
        self.assertEqual(fixture.ruleset, original)
        self.assertEqual(fixture.writes, [])

    def test_matching_configuration_never_writes(self):
        fixture = GithubFixture()
        fixture.ruleset["rules"][2]["parameters"]["server_default"] = False
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.writes, [])

    def test_existing_stricter_pull_request_protection_is_not_weakened(self):
        fixture = GithubFixture()
        parameters = fixture.ruleset["rules"][2]["parameters"]
        parameters.update(required_approving_review_count=2, dismiss_stale_reviews_on_push=True,
                          require_code_owner_review=True, require_last_push_approval=True,
                          required_review_thread_resolution=True)
        expected = copy.deepcopy(parameters)
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.ruleset["rules"][2]["parameters"], expected)
        self.assertEqual(fixture.writes, [])

    def test_check_reports_missing_configuration_without_writing(self):
        fixture = GithubFixture()
        fixture.ruleset = None
        fixture.repo["allow_merge_commit"] = True
        self.assertEqual(self.run_setup(fixture, "--check", "--release-app-id", "12345"), 1)
        self.assertEqual(fixture.writes, [])

    def test_only_missing_settings_are_applied_and_read_back(self):
        fixture = GithubFixture()
        fixture.ruleset = None
        fixture.reporting = False
        fixture.repo["allow_merge_commit"] = True
        self.assertEqual(self.run_setup(fixture, "--release-app-id", "12345"), 0)
        self.assertEqual([call[1] for call in fixture.writes], ["PATCH", "POST", "PUT"])
        self.assertEqual(fixture.writes[0][2], {"allow_merge_commit": False})
        self.assertEqual(fixture.writes[1][2]["bypass_actors"], [RELEASE_ACTOR])
        fixture.calls.clear()
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.writes, [])

    def test_missing_ci_check_prevents_every_write(self):
        fixture = GithubFixture()
        fixture.checks.remove("verified")
        fixture.repo["allow_merge_commit"] = True
        with self.assertRaisesRegex(RuntimeError, "verified"):
            self.run_setup(fixture)
        self.assertEqual(fixture.writes, [])

    def test_ci_jobs_are_paginated(self):
        fixture = GithubFixture()
        fixture.checks = [f"matrix-{index}" for index in range(100)] + CHECKS
        self.assertEqual(self.run_setup(fixture, "--check"), 0)

    def test_native_repository_requires_both_native_checks_before_writing(self):
        fixture = GithubFixture()
        fixture.native = True
        with self.assertRaisesRegex(RuntimeError, "lint-cpp, lint-kotlin"):
            self.run_setup(fixture)
        self.assertEqual(fixture.writes, [])
        fixture.native_checks = ["lint-cpp", "lint-kotlin"]
        self.assertEqual(self.run_setup(fixture), 0)
        checks = fixture.ruleset["rules"][3]["parameters"]["required_status_checks"]
        self.assertEqual({check["context"] for check in checks}, set(CHECKS + fixture.native_checks))
        self.assertEqual([call[1] for call in fixture.writes], ["PUT"])

    def test_unknown_security_state_is_not_assumed_disabled(self):
        fixture = GithubFixture()
        fixture.repo["allow_merge_commit"] = True
        del fixture.repo["security_and_analysis"]["dependabot_security_updates"]
        with self.assertRaisesRegex(RuntimeError, "未取得自动安全更新状态"):
            self.run_setup(fixture)
        self.assertEqual(fixture.writes, [])

    def test_disable_automatic_security_prs_only_when_enabled(self):
        fixture = GithubFixture()
        fixture.repo["security_and_analysis"]["dependabot_security_updates"]["status"] = "enabled"
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.writes, [(BASE + "/automated-security-fixes", "DELETE", None)])

    def test_add_required_check_without_dropping_existing_checks(self):
        fixture = GithubFixture()
        checks = fixture.ruleset["rules"][3]["parameters"]["required_status_checks"]
        checks[:] = [check for check in checks if check["context"] != "verified"]
        checks[0]["integration_id"] = 456
        checks.append({"context": "custom-check", "integration_id": 123})
        fixture.ruleset["rules"].append({"type": "required_signatures"})
        self.assertEqual(self.run_setup(fixture), 0)
        result = fixture.ruleset["rules"][3]["parameters"]["required_status_checks"]
        self.assertIn({"context": "custom-check", "integration_id": 123}, result)
        self.assertIn({"context": "actionlint", "integration_id": 456}, result)
        self.assertIn({"context": "verified"}, result)
        self.assertIn({"type": "required_signatures"}, fixture.ruleset["rules"])

    def test_failed_read_back_does_not_report_success(self):
        fixture = GithubFixture()
        fixture.ruleset = None
        fixture.ignore_writes = True
        with self.assertRaisesRegex(RuntimeError, "回读仍有差异"):
            self.run_setup(fixture, "--release-app-id", "12345")

    def test_pages_are_created_only_with_the_deployment_workflow(self):
        fixture = GithubFixture()
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertFalse(any(call[0].endswith("/pages") for call in fixture.calls))
        fixture.website = True
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.repo["homepage"], fixture.site["html_url"])
        fixture.calls.clear()
        self.assertEqual(self.run_setup(fixture), 0)
        self.assertEqual(fixture.writes, [])

    def test_non_admin_stops_before_mutations(self):
        fixture = GithubFixture()
        fixture.repo["permissions"]["admin"] = False
        with self.assertRaisesRegex(RuntimeError, "管理员权限"):
            self.run_setup(fixture)
        self.assertEqual(fixture.writes, [])

    def test_api_forbidden_is_not_treated_as_missing(self):
        result = type("Result", (), {"returncode": 1, "stderr": "gh: Forbidden (HTTP 403)", "stdout": ""})()
        with patch.object(setup.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
                setup.api("repos/example/fixture/contents/file", missing_ok=True)
        result.stderr = "gh: Not Found (HTTP 404)"
        with patch.object(setup.subprocess, "run", return_value=result):
            self.assertIsNone(setup.api("repos/example/fixture/contents/file", missing_ok=True))


if __name__ == "__main__":
    unittest.main()
