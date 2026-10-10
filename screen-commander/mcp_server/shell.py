"""Headless zsh execution for Screen Commander MCP.

Auth / allow-list: same as every other MCP tool on this server — no per-tool
token or command allow-list. Access is gated only by the shared transport
settings in ``server.transport_security_settings`` (``MCP_ALLOWED_HOSTS`` /
``MCP_ALLOWED_ORIGINS`` / ``MCP_DISABLE_DNS_REBINDING``).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from typing import Any


DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 300
# Cap captured output so a runaway `yes` can't blow memory.
MAX_OUTPUT_BYTES = 2 * 1024 * 1024


def run_shell(command: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """
    Run ``command`` with ``/bin/zsh -lc`` (login shell for PATH/Homebrew).

    Headless via subprocess (no Terminal.app). On timeout the process group is
    killed (SIGTERM then SIGKILL). Returns JSON-serializable
    ``{stdout, stderr, exit_code}`` (``exit_code`` is ``-1`` on timeout).

    No separate auth: inherits the server transport allow-list used by
    ``computer`` / legacy mouse tools.
    """
    if not isinstance(command, str) or not command.strip():
        raise ValueError("command must be a non-empty string")

    try:
        timeout_s = int(timeout)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"timeout must be an integer number of seconds, got {timeout!r}") from exc
    if timeout_s <= 0:
        raise ValueError("timeout must be > 0")
    timeout_s = min(timeout_s, MAX_TIMEOUT)

    env = os.environ.copy()
    env.setdefault("TERM", "dumb")

    # New session/process group so timeout can kill pipelines and children.
    proc = subprocess.Popen(
        ["/bin/zsh", "-lc", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        start_new_session=True,
    )

    try:
        stdout_b, stderr_b = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill_process_group(proc)
        try:
            stdout_b, stderr_b = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            stdout_b, stderr_b = b"", b""
        stdout = _decode_capped(stdout_b)
        stderr = _decode_capped(stderr_b)
        note = f"[run_shell] timed out after {timeout_s}s; process group killed"
        stderr = f"{stderr}\n{note}".strip() if stderr else note
        return _result(stdout, stderr, -1)

    return _result(
        _decode_capped(stdout_b),
        _decode_capped(stderr_b),
        int(proc.returncode if proc.returncode is not None else -1),
    )


def run_shell_json(command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Same as :func:`run_shell`, serialized as a JSON object string."""
    return json.dumps(run_shell(command, timeout=timeout), ensure_ascii=False)


def _result(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
    }


def _kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    """Terminate the shell and any children, then force-kill if needed."""
    if proc.pid is None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.05)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass


def _decode_capped(data: bytes | None) -> str:
    if not data:
        return ""
    truncated = False
    if len(data) > MAX_OUTPUT_BYTES:
        data = data[:MAX_OUTPUT_BYTES]
        truncated = True
    text = data.decode("utf-8", errors="replace")
    if truncated:
        text += f"\n[run_shell] output truncated at {MAX_OUTPUT_BYTES} bytes"
    return text
