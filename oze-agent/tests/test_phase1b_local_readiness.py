from pathlib import Path

from scripts.run_phase1b_local_readiness import (
    ReadinessConfig,
    Step,
    StepResult,
    build_steps,
    redact_command,
    render_markdown_report,
    run_steps,
)


def _config(tmp_path: Path, **overrides) -> ReadinessConfig:
    values = {
        "oze_agent_dir": tmp_path / "oze-agent",
        "web_dir": tmp_path / "web",
        "web_env_file": None,
        "api_env_file": None,
        "web_base_url": None,
        "api_base_url": None,
        "full_backend": False,
    }
    values.update(overrides)
    return ReadinessConfig(**values)


def test_orchestrator_builds_static_checks_without_smoke_urls(tmp_path):
    steps = build_steps(_config(tmp_path))

    names = [step.name for step in steps]

    assert "python runtime" in names
    assert names[0] == "python runtime"
    assert "web unit tests" in names
    assert "web smoke" in names
    assert "api smoke" in names
    assert next(step for step in steps if step.name == "web smoke").skip_reason
    assert next(step for step in steps if step.name == "api smoke").skip_reason
    assert "full backend tests" not in names


def test_orchestrator_adds_smoke_and_full_backend_when_requested(tmp_path):
    steps = build_steps(
        _config(
            tmp_path,
            web_base_url="http://127.0.0.1:3001",
            api_base_url="http://127.0.0.1:8010",
            full_backend=True,
        )
    )

    web_smoke = next(step for step in steps if step.name == "web smoke")
    api_smoke = next(step for step in steps if step.name == "api smoke")

    assert web_smoke.skip_reason is None
    assert "--base-url=http://127.0.0.1:3001" in web_smoke.command
    assert api_smoke.skip_reason is None
    assert "--base-url=http://127.0.0.1:8010" in api_smoke.command
    assert "full backend tests" in [step.name for step in steps]


def test_orchestrator_resolves_env_files_to_absolute_paths(tmp_path):
    web_env = tmp_path / "web.env"
    api_env = tmp_path / "api.env"
    steps = build_steps(
        _config(tmp_path, web_env_file=web_env, api_env_file=api_env)
    )

    web_env_step = next(step for step in steps if step.name == "web env")
    api_env_step = next(step for step in steps if step.name == "api env")

    assert f"--env-file={web_env.resolve()}" in web_env_step.command
    assert f"--env-file={api_env.resolve()}" in api_env_step.command


def test_orchestrator_checks_python_runtime_before_backend_steps(tmp_path):
    steps = build_steps(_config(tmp_path))

    names = [step.name for step in steps]
    runtime_index = names.index("python runtime")

    assert runtime_index < names.index("api env")
    assert names.index("web unit tests") < names.index("web lint")
    assert "3, 13" in " ".join(steps[runtime_index].command)
    assert steps[runtime_index].stop_on_failure is True


def test_orchestrator_stops_after_critical_failure(tmp_path):
    steps = [
        Step(
            name="critical",
            command=["/bin/sh", "-c", "echo bad; exit 7"],
            cwd=tmp_path,
            stop_on_failure=True,
        ),
        Step(
            name="after",
            command=["/bin/sh", "-c", "echo should-not-run"],
            cwd=tmp_path,
        ),
    ]

    results = run_steps(steps)

    assert [result.name for result in results] == ["critical"]
    assert results[0].status == "failed"
    assert results[0].exit_code == 7


def test_orchestrator_redacts_env_file_arguments(tmp_path):
    command = [
        "python3",
        "scripts/verify_phase1b_env.py",
        f"--env-file={tmp_path / 'secret.env'}",
    ]

    assert str(tmp_path) not in redact_command(command)
    assert "--env-file=<redacted-path>" in redact_command(command)


def test_report_does_not_include_env_file_paths_or_secret_values(tmp_path):
    result = StepResult(
        name="api env",
        status="passed",
        command=[
            "python3",
            "scripts/verify_phase1b_env.py",
            f"--env-file={tmp_path / 'secret.env'}",
        ],
        cwd=tmp_path,
        duration_seconds=0.12,
        exit_code=0,
        output=(
            "> node scripts/check-phase1b-env.mjs --env-file=/tmp/secret.env\n"
            "Loaded env file(s): /tmp/secret.env\n"
            "Phase 1B FastAPI env OK"
        ),
    )

    report = render_markdown_report([result], started_at="2026-04-29 12:00")

    assert str(tmp_path) not in report
    assert "secret.env" not in report
    assert "--env-file=<redacted-path>" in report
    assert "Loaded env file(s): <redacted>" in report
