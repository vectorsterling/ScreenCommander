"""Full-screen human-help overlay for Screen Commander MCP.

Shows the request on an always-on-top overlay and blocks until the human
clicks Done or 5 minutes elapse. A chime plays when the wait starts and
every 30 seconds after that. The overlay process is a subprocess so AppKit
runs on that process's main thread; this module only waits and plays sound.

Dismissal is Done or timeout only: the panels are borderless, ignore close,
and refuse application terminate.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


TIMEOUT_SECONDS = 300
CHIME_INTERVAL_SECONDS = 30
# How often the waiter rechecks the overlay process between chimes.
POLL_INTERVAL_SECONDS = 0.2
SOUND_PATH = "/System/Library/Sounds/Sosumi.aiff"
# Child exit codes: 0 Done, 2 timeout, anything else is a failure.
_EXIT_COMPLETED = 0
_EXIT_TIMEOUT = 2


def human_help(text: str) -> dict[str, Any]:
    """Show ``text`` and wait for Done, or time out after 5 minutes.

    Returns ``{success, status, detail}``. ``status`` is ``completed`` when
    the human clicks Done, ``timeout`` if 5 minutes pass, or ``failed`` if
    the overlay ends another way.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")

    session = _open_overlay(text.strip(), TIMEOUT_SECONDS)
    try:
        status = _wait_until_done(
            session.poll_status,
            timeout_seconds=TIMEOUT_SECONDS,
            chime_interval_seconds=CHIME_INTERVAL_SECONDS,
            play_sound=_play_chime,
        )
    finally:
        session.close()
    return _response(status)


def _response(status: str) -> dict[str, Any]:
    if status == "completed":
        return {
            "success": True,
            "status": "completed",
            "detail": "Human clicked Done.",
        }
    if status == "timeout":
        return {
            "success": False,
            "status": "timeout",
            "detail": "Done was not clicked within 5 minutes.",
        }
    return {
        "success": False,
        "status": "failed",
        "detail": "Overlay ended before Done was clicked.",
    }


def _play_chime() -> None:
    """Play Sosumi without waiting for ``afplay`` to finish."""
    try:
        subprocess.Popen(
            ["afplay", SOUND_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return


def _wait_until_done(
    poll_status: Callable[[], str | None],
    *,
    timeout_seconds: float,
    chime_interval_seconds: float,
    play_sound: Callable[[], None],
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Wait until ``poll_status`` reports an outcome or the deadline passes.

    ``poll_status`` returns ``"completed"``, ``"timeout"``, ``"failed"``, or
    ``None`` while still waiting. A chime plays immediately and then every
    ``chime_interval_seconds`` for as long as the wait continues.
    """
    if timeout_seconds <= 0:
        return "timeout"

    start = monotonic()
    deadline = start + timeout_seconds
    next_chime = start
    while True:
        now = monotonic()
        if now >= deadline:
            return "timeout"
        status = poll_status()
        if status in {"completed", "timeout", "failed"}:
            return status
        if now >= next_chime:
            play_sound()
            next_chime += chime_interval_seconds
        remaining = min(deadline, next_chime) - monotonic()
        sleep(min(POLL_INTERVAL_SECONDS, max(0.0, remaining)))


class _OverlayProcess:
    def __init__(self, proc: subprocess.Popen[bytes]) -> None:
        self.proc = proc

    def poll_status(self) -> str | None:
        code = self.proc.poll()
        if code is None:
            return None
        if code == _EXIT_COMPLETED:
            return "completed"
        if code == _EXIT_TIMEOUT:
            return "timeout"
        return "failed"

    def close(self) -> None:
        if self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                return


def _open_overlay(message: str, timeout_seconds: float) -> _OverlayProcess:
    """Start the AppKit overlay subprocess. The message is written to stdin."""
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    previous = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(root) + (os.pathsep + previous if previous else "")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "mcp_server.human_help",
            "--overlay",
            str(timeout_seconds),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=None,
        cwd=str(root),
        env=env,
    )
    assert proc.stdin is not None
    proc.stdin.write(message.encode("utf-8"))
    proc.stdin.close()
    return _OverlayProcess(proc)


def run_fullscreen_overlay(message: str, *, timeout_seconds: float) -> str:
    """Show a full-screen always-on-top overlay. Return ``completed`` or ``timeout``.

    A dim panel covers every display and ignores mouse events so the human can
    still use the screen. The message and Done button sit in a separate
    always-on-top card on the main display. Neither panel has a close control.
    """
    import objc
    from AppKit import (
        NSAnyEventMask,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSBackingStoreBuffered,
        NSBezierPath,
        NSButton,
        NSColor,
        NSFont,
        NSFontAttributeName,
        NSForegroundColorAttributeName,
        NSMakeRect,
        NSMakeSize,
        NSMutableParagraphStyle,
        NSNoBorder,
        NSParagraphStyleAttributeName,
        NSScreen,
        NSStatusWindowLevel,
        NSScrollView,
        NSTerminateCancel,
        NSTextAlignmentCenter,
        NSTextView,
        NSViewWidthSizable,
        NSWindow,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorFullScreenAuxiliary,
        NSWindowCollectionBehaviorStationary,
        NSWindowStyleMaskBorderless,
    )
    from Foundation import NSDate, NSDefaultRunLoopMode, NSObject, NSString

    class _OverlayController(NSObject):
        def init(self):  # type: ignore[no-untyped-def]
            self = objc.super(_OverlayController, self).init()
            if self is None:
                return None
            self.done = False
            return self

        def complete_(self, _sender) -> None:  # type: ignore[no-untyped-def]
            self.done = True

        def windowShouldClose_(self, _sender) -> bool:  # type: ignore[no-untyped-def]
            return False

        def applicationShouldTerminate_(self, _sender):  # type: ignore[no-untyped-def]
            return NSTerminateCancel

    class _LockedPanel(NSWindow):
        """Borderless window that ignores close, Escape, and Command-W."""

        def initWithContentRect_styleMask_backing_defer_(self, rect, style, backing, defer):  # type: ignore[no-untyped-def]
            self = objc.super(_LockedPanel, self).initWithContentRect_styleMask_backing_defer_(
                rect, style, backing, defer
            )
            if self is None:
                return None
            self._allowClose = False
            return self

        def close(self) -> None:  # type: ignore[override]
            if self._allowClose:
                objc.super(_LockedPanel, self).close()

        def performClose_(self, _sender) -> None:  # type: ignore[no-untyped-def]
            return None

        def keyDown_(self, _event) -> None:  # type: ignore[no-untyped-def]
            return None

        def cancelOperation_(self, _sender) -> None:  # type: ignore[no-untyped-def]
            return None

    class _DoneButton(NSButton):
        """Yellow Done button. The system bezel stays gray when the panel is not key."""

        def drawRect_(self, _dirty) -> None:  # type: ignore[no-untyped-def]
            bounds = self.bounds()
            NSColor.systemYellowColor().setFill()
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 14, 14)
            path.fill()
            NSColor.blackColor().setStroke()
            path.setLineWidth_(3)
            path.stroke()
            style = NSMutableParagraphStyle.alloc().init()
            style.setAlignment_(NSTextAlignmentCenter)
            attrs = {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(30),
                NSForegroundColorAttributeName: NSColor.blackColor(),
                NSParagraphStyleAttributeName: style,
            }
            title = NSString.stringWithString_(self.title() or "Done")
            text_size = title.sizeWithAttributes_(attrs)
            x = (bounds.size.width - text_size.width) / 2.0
            y = (bounds.size.height - text_size.height) / 2.0
            title.drawAtPoint_withAttributes_((x, y), attrs)

    screens = NSScreen.screens()
    if not screens:
        raise RuntimeError("No displays available for the human_help overlay")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = _OverlayController.alloc().init()
    app.setDelegate_(controller)

    style = NSWindowStyleMaskBorderless
    # Above normal windows, the Dock, and the menu bar. NSPanel clamps setLevel_
    # back to the floating level, so these are NSWindows.
    backdrop_level = int(NSStatusWindowLevel)
    card_level = backdrop_level + 1
    behavior = (
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorFullScreenAuxiliary
        | NSWindowCollectionBehaviorStationary
    )
    windows: list[Any] = []

    def _present(panel: _LockedPanel, level: int) -> None:
        panel.setLevel_(level)
        panel.setCollectionBehavior_(behavior)
        panel.setHidesOnDeactivate_(False)
        panel.setCanHide_(False)
        panel.setMovable_(False)
        panel.setMovableByWindowBackground_(False)
        panel.setReleasedWhenClosed_(False)
        panel.setExcludedFromWindowsMenu_(True)
        panel.setHasShadow_(False)
        panel.setDelegate_(controller)
        panel.orderFrontRegardless()
        windows.append(panel)

    for screen in screens:
        backdrop = _LockedPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            screen.frame(),
            style,
            NSBackingStoreBuffered,
            False,
        )
        backdrop.setOpaque_(False)
        backdrop.setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.45))
        backdrop.setIgnoresMouseEvents_(True)
        _present(backdrop, backdrop_level)

    main = NSScreen.mainScreen() or screens[0]
    frame = main.frame()
    card_w = min(920.0, max(520.0, float(frame.size.width) - 80.0))
    card_h = min(420.0, max(280.0, float(frame.size.height) * 0.36))
    card_x = float(frame.origin.x) + (float(frame.size.width) - card_w) / 2.0
    card_y = float(frame.origin.y) + float(frame.size.height) - card_h - 36.0
    card = _LockedPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(card_x, card_y, card_w, card_h),
        style,
        NSBackingStoreBuffered,
        False,
    )
    card.setOpaque_(False)
    card.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.07, 0.08, 0.11, 0.97))
    card.setIgnoresMouseEvents_(False)

    padding = 28.0
    button_w, button_h = 280.0, 76.0
    text_x = padding
    text_w = card_w - 2 * padding
    text_y = padding + button_h + 20.0
    text_h = card_h - text_y - padding

    scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(text_x, text_y, text_w, text_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    scroll.setBorderType_(NSNoBorder)
    scroll.setDrawsBackground_(False)

    text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, text_w, text_h))
    text_view.setString_(message)
    text_view.setEditable_(False)
    text_view.setSelectable_(False)
    text_view.setDrawsBackground_(False)
    text_view.setRichText_(False)
    text_view.setTextColor_(NSColor.whiteColor())
    text_view.setFont_(NSFont.systemFontOfSize_(26))
    text_view.setAlignment_(NSTextAlignmentCenter)
    text_view.setHorizontallyResizable_(False)
    text_view.setVerticallyResizable_(True)
    text_view.setAutoresizingMask_(NSViewWidthSizable)
    container = text_view.textContainer()
    container.setWidthTracksTextView_(True)
    container.setContainerSize_(NSMakeSize(text_w - 8, 10_000_000))
    scroll.setDocumentView_(text_view)
    card.contentView().addSubview_(scroll)

    button = _DoneButton.alloc().initWithFrame_(
        NSMakeRect((card_w - button_w) / 2.0, padding, button_w, button_h)
    )
    button.setTitle_("Done")
    button.setBordered_(False)
    button.setTarget_(controller)
    button.setAction_("complete:")
    card.contentView().addSubview_(button)

    _present(card, card_level)

    # Drain AppKit events explicitly. runMode: alone leaves clicks queued, so
    # the Done button never sees them.
    deadline = time.monotonic() + timeout_seconds
    while not controller.done:
        if time.monotonic() >= deadline:
            _close_panels(windows)
            return "timeout"
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            NSAnyEventMask,
            NSDate.dateWithTimeIntervalSinceNow_(0.1),
            NSDefaultRunLoopMode,
            True,
        )
        if event is not None:
            app.sendEvent_(event)
            app.updateWindows()
    _close_panels(windows)
    return "completed"


def _close_panels(windows: list[Any]) -> None:
    for window in windows:
        window._allowClose = True
        window.orderOut_(None)
        window.close()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "--overlay":
        print(
            "usage: python -m mcp_server.human_help --overlay [timeout_seconds]",
            file=sys.stderr,
        )
        return 1
    timeout = float(TIMEOUT_SECONDS if len(args) == 1 else args[1])
    message = sys.stdin.read()
    if not message.strip():
        print("overlay message is empty", file=sys.stderr)
        return 1
    try:
        status = run_fullscreen_overlay(message.strip(), timeout_seconds=timeout)
    except Exception as exc:
        print(f"human_help overlay failed: {exc}", file=sys.stderr)
        return 1
    if status == "completed":
        return _EXIT_COMPLETED
    if status == "timeout":
        return _EXIT_TIMEOUT
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
