from mcp_server.shell import run_shell, run_shell_json
import json


def test_run_shell_echo():
    result = run_shell("echo hello-from-zsh", timeout=10)
    assert result["exit_code"] == 0
    assert "hello-from-zsh" in result["stdout"]
    assert result["stderr"] == ""
    # Structured JSON round-trip
    parsed = json.loads(run_shell_json("echo hello-from-zsh", timeout=10))
    assert parsed["exit_code"] == 0
    assert set(parsed) == {"stdout", "stderr", "exit_code"}


def test_run_shell_nonzero_exit():
    result = run_shell("exit 7", timeout=10)
    assert result["exit_code"] == 7


def test_run_shell_timeout_kills():
    # Pipeline children should die with the process group.
    result = run_shell("sleep 60 | sleep 60", timeout=1)
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"]
    assert "killed" in result["stderr"]


def test_run_shell_rejects_empty():
    try:
        run_shell("  ", timeout=5)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "non-empty" in str(exc)
