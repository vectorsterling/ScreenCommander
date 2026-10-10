import subprocess

from mcp_server.human_help import _play_chime, _wait_until_done, human_help


def test_human_help_rejects_empty():
    try:
        human_help("  ")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "non-empty" in str(exc)


def test_human_help_rejects_non_string():
    try:
        human_help(None)  # type: ignore[arg-type]
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "non-empty" in str(exc) or "string" in str(exc)


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


def test_wait_chimes_every_30s_then_times_out():
    clock = _Clock()
    sounds: list[float] = []
    status = _wait_until_done(
        lambda: None,
        timeout_seconds=300,
        chime_interval_seconds=30,
        play_sound=lambda: sounds.append(clock.t),
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    assert status == "timeout"
    assert sounds == [30 * i for i in range(10)]
    assert clock.t == 300


def test_wait_returns_when_done_is_clicked():
    clock = _Clock()
    polls = {"n": 0}

    def poll() -> str | None:
        polls["n"] += 1
        return "completed" if polls["n"] >= 2 else None

    status = _wait_until_done(
        poll,
        timeout_seconds=300,
        chime_interval_seconds=30,
        play_sound=lambda: None,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    assert status == "completed"
    assert clock.t < 30


def test_human_help_completed(monkeypatch):
    class Session:
        def __init__(self) -> None:
            self.closed = False

        def poll_status(self) -> str:
            return "completed"

        def close(self) -> None:
            self.closed = True

    session = Session()
    monkeypatch.setattr("mcp_server.human_help._open_overlay", lambda text, timeout: session)
    result = human_help("Please complete the check, then click Done.")
    assert result == {
        "success": True,
        "status": "completed",
        "detail": "Human clicked Done.",
    }
    assert session.closed is True


def test_human_help_timeout(monkeypatch):
    class Session:
        def __init__(self) -> None:
            self.closed = False

        def poll_status(self) -> None:
            return None

        def close(self) -> None:
            self.closed = True

    session = Session()
    monkeypatch.setattr("mcp_server.human_help._open_overlay", lambda text, timeout: session)
    monkeypatch.setattr("mcp_server.human_help._wait_until_done", lambda *args, **kwargs: "timeout")
    result = human_help("Need a human to finish the prompt.")
    assert result["success"] is False
    assert result["status"] == "timeout"
    assert "5 minutes" in result["detail"]
    assert session.closed is True


def test_play_chime_is_nonblocking_afplay(monkeypatch):
    calls: list[tuple[list[str], dict]] = []

    def fake_popen(args, **kwargs):
        calls.append((list(args), kwargs))
        return object()

    monkeypatch.setattr("mcp_server.human_help.subprocess.Popen", fake_popen)
    _play_chime()
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == ["afplay", "/System/Library/Sounds/Sosumi.aiff"]
    assert kwargs["start_new_session"] is True
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL


def test_server_registers_human_help():
    from mcp_server.server import create_server

    tool = create_server()._tool_manager.get_tool("human_help")
    assert tool is not None
    assert tool.name == "human_help"
    assert "text" in tool.parameters.get("properties", {})
