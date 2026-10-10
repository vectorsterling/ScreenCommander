import Foundation
import CoreGraphics // For CGPoint, CGEventFlags
import MacosUseSDK // Import the library

// --- Start Time ---
let startTime = Date() // Record start time for the tool's execution

// --- Helper Function for Logging ---
// Tool-specific logging prefix
func log(_ message: String) {
    fputs("InputControllerTool: \(message)\n", stderr)
}

// --- Helper Function for Exiting ---
// Logs final time and exits
func finish(success: Bool, message: String? = nil) -> Never {
    if let msg = message {
        log(success ? "✅ Success: \(msg)" : "❌ Error: \(msg)")
    }

    // --- Calculate and Log Time ---
    let endTime = Date()
    let processingTime = endTime.timeIntervalSince(startTime)
    let formattedTime = String(format: "%.3f", processingTime)
    fputs("InputControllerTool: total execution time: \(formattedTime) seconds\n", stderr)
    // --- End Time Logging ---

    exit(success ? 0 : 1)
}


// --- Argument Parsing and Main Logic ---
let arguments = CommandLine.arguments
let scriptName = arguments.first ?? "InputControllerTool"

// Define usage instructions
let usage = """
usage: \(scriptName) <action> [options...]

actions:
  keypress <key_name_or_code>[+modifier...]   Simulate pressing a key (e.g., 'return', 'a', 'f1', 'cmd+c', 'shift+tab').
                                             Supported modifiers: cmd, shift, opt, ctrl, fn.
  holdkey <key_combo> <duration_seconds>     Hold key/combo down for duration (max 30s).
  click <x> <y> [modifiers] [clickCount]     Left click (optional mods e.g. cmd+shift, optional count 1-3).
  doubleclick <x> <y> [modifiers]
  tripleclick <x> <y> [modifiers]
  rightclick <x> <y> [modifiers]
  middleclick <x> <y> [modifiers]
  mousedown <x> <y>                          Left button down (hold).
  mouseup <x> <y>                            Left button up.
  mousemove <x> <y>                          Move cursor.
  mousedragto <x> <y>                        Move with leftMouseDragged (button must be held).
  drag <x1> <y1> <x2> <y2> [steps] [mods]    Press, drag with interpolated dragged events, release.
  writetext <text_to_type>                   Simulate typing a string of text.
  scroll <x> <y> <deltaY> <deltaX> [mods]    Scroll; deltaX uses horizontal wheel axis 2.
  cursorpos                                  Print current cursor x y (Quartz points).

Examples:
  \(scriptName) keypress enter
  \(scriptName) keypress cmd+shift+4
  \(scriptName) holdkey shift 2.5
  \(scriptName) click 100 250
  \(scriptName) click 100 250 cmd+shift 1
  \(scriptName) tripleclick 100 250
  \(scriptName) middleclick 100 250
  \(scriptName) drag 100 100 400 300 16
  \(scriptName) writetext "Hello World!"
  \(scriptName) scroll 500 500 -10 0
  \(scriptName) scroll 500 500 0 10 shift
"""

// Shared key-combo parser: "cmd+shift+a" → (keyCode, flags)
func parseKeyCombo(_ keyCombo: String) throws -> (CGKeyCode, CGEventFlags) {
    let parts = keyCombo.split(separator: "+").map { String($0).trimmingCharacters(in: .whitespacesAndNewlines).lowercased() }
    guard let keyPart = parts.last else {
        throw MacosUseSDKError.inputInvalidArgument("Invalid key combination format: '\(keyCombo)'")
    }
    var flags: CGEventFlags = []
    if parts.count > 1 {
        for i in 0..<(parts.count - 1) {
            switch parts[i] {
            case "cmd", "command", "super", "win", "meta": flags.insert(.maskCommand)
            case "shift": flags.insert(.maskShift)
            case "opt", "option", "alt": flags.insert(.maskAlternate)
            case "ctrl", "control": flags.insert(.maskControl)
            case "fn", "function": flags.insert(.maskSecondaryFn)
            default: throw MacosUseSDKError.inputInvalidArgument("Unknown modifier: '\(parts[i])' in '\(keyCombo)'")
            }
        }
    }
    guard let keyCode = MacosUseSDK.mapKeyNameToKeyCode(keyPart) else {
        throw MacosUseSDKError.inputInvalidArgument("Unknown key name or invalid key code: '\(keyPart)' in '\(keyCombo)'")
    }
    return (keyCode, flags)
}

/// Parse modifier-only string ("cmd", "shift+alt") into flags. Empty → [].
func parseModifierFlags(_ text: String?) throws -> CGEventFlags {
    guard let text = text?.trimmingCharacters(in: .whitespacesAndNewlines), !text.isEmpty else {
        return []
    }
    var flags: CGEventFlags = []
    let parts = text.split(separator: "+").map { String($0).trimmingCharacters(in: .whitespacesAndNewlines).lowercased() }
    for part in parts {
        switch part {
        case "cmd", "command", "super", "win", "meta": flags.insert(.maskCommand)
        case "shift": flags.insert(.maskShift)
        case "opt", "option", "alt": flags.insert(.maskAlternate)
        case "ctrl", "control": flags.insert(.maskControl)
        case "fn", "function": flags.insert(.maskSecondaryFn)
        default:
            throw MacosUseSDKError.inputInvalidArgument(
                "Unknown modifier '\(part)'. Valid: cmd, shift, alt/option, ctrl, fn (combine with +)."
            )
        }
    }
    return flags
}

func requireDouble(_ raw: String, label: String) throws -> Double {
    guard let value = Double(raw) else {
        throw MacosUseSDKError.inputInvalidArgument("Invalid \(label): '\(raw)' must be a number.")
    }
    return value
}

// Check for minimum argument count
guard arguments.count > 1 else {
    fputs(usage, stderr)
    finish(success: false, message: "No action specified.")
}

let action = arguments[1].lowercased()
log("Action: \(action)")

// --- Action Handling ---
do {
    switch action {
    case "keypress":
        guard arguments.count == 3 else {
            throw MacosUseSDKError.inputInvalidArgument("'keypress' requires exactly one argument: <key_name_or_code_with_modifiers>\n\(usage)")
        }
        let keyCombo = arguments[2]
        log("Key Combo Argument: '\(keyCombo)'")
        let (finalKeyCode, flags) = try parseKeyCombo(keyCombo)
        log("Calling pressKey library function...")
        try MacosUseSDK.pressKey(keyCode: finalKeyCode, flags: flags)
        finish(success: true, message: "Key press '\(keyCombo)' simulated.")

    case "holdkey":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'holdkey' requires <key_combo> <duration_seconds>")
        }
        let keyCombo = arguments[2]
        let duration = try requireDouble(arguments[3], label: "duration")
        let (keyCode, flags) = try parseKeyCombo(keyCombo)
        try MacosUseSDK.holdKey(keyCode: keyCode, flags: flags, duration: duration)
        finish(success: true, message: "Held '\(keyCombo)' for \(min(max(duration, 0), 30))s.")

    case "click", "doubleclick", "tripleclick", "rightclick", "middleclick":
        guard arguments.count >= 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'\(action)' requires <x> <y> [modifiers] [clickCount]")
        }
        let x = try requireDouble(arguments[2], label: "x")
        let y = try requireDouble(arguments[3], label: "y")
        let point = CGPoint(x: x, y: y)
        var mods: String? = nil
        var countOverride: Int64? = nil
        if arguments.count >= 5 {
            if let asInt = Int64(arguments[4]), arguments.count == 5 {
                countOverride = asInt
            } else {
                mods = arguments[4]
                if arguments.count >= 6, let asInt = Int64(arguments[5]) {
                    countOverride = asInt
                }
            }
        }
        let flags = try parseModifierFlags(mods)
        let button: CGMouseButton
        let clickCount: Int64
        switch action {
        case "rightclick":
            button = .right; clickCount = countOverride ?? 1
        case "middleclick":
            button = .center; clickCount = countOverride ?? 1
        case "doubleclick":
            button = .left; clickCount = countOverride ?? 2
        case "tripleclick":
            button = .left; clickCount = countOverride ?? 3
        default:
            button = .left; clickCount = countOverride ?? 1
        }
        try MacosUseSDK.clickMouse(at: point, button: button, clickCount: clickCount, flags: flags)
        finish(success: true, message: "\(action) simulated at (\(x), \(y)).")

    case "mousedown":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'mousedown' requires <x> <y>")
        }
        let point = CGPoint(x: try requireDouble(arguments[2], label: "x"), y: try requireDouble(arguments[3], label: "y"))
        try MacosUseSDK.mouseButtonDown(at: point, button: .left)
        finish(success: true, message: "Left mouse down at (\(point.x), \(point.y)).")

    case "mouseup":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'mouseup' requires <x> <y>")
        }
        let point = CGPoint(x: try requireDouble(arguments[2], label: "x"), y: try requireDouble(arguments[3], label: "y"))
        try MacosUseSDK.mouseButtonUp(at: point, button: .left)
        finish(success: true, message: "Left mouse up at (\(point.x), \(point.y)).")

    case "mousemove":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'mousemove' requires <x> <y>")
        }
        let point = CGPoint(x: try requireDouble(arguments[2], label: "x"), y: try requireDouble(arguments[3], label: "y"))
        try MacosUseSDK.moveMouse(to: point)
        finish(success: true, message: "mousemove simulated at (\(point.x), \(point.y)).")

    case "mousedragto":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'mousedragto' requires <x> <y>")
        }
        let point = CGPoint(x: try requireDouble(arguments[2], label: "x"), y: try requireDouble(arguments[3], label: "y"))
        try MacosUseSDK.moveMouse(to: point, dragging: true)
        finish(success: true, message: "mousedragto simulated at (\(point.x), \(point.y)).")

    case "drag":
        guard arguments.count >= 6 else {
            throw MacosUseSDKError.inputInvalidArgument("'drag' requires <x1> <y1> <x2> <y2> [steps] [modifiers]")
        }
        let start = CGPoint(x: try requireDouble(arguments[2], label: "x1"), y: try requireDouble(arguments[3], label: "y1"))
        let end = CGPoint(x: try requireDouble(arguments[4], label: "x2"), y: try requireDouble(arguments[5], label: "y2"))
        var steps = 16
        var mods: String? = nil
        if arguments.count >= 7 {
            if let s = Int(arguments[6]) {
                steps = s
                if arguments.count >= 8 { mods = arguments[7] }
            } else {
                mods = arguments[6]
            }
        }
        let flags = try parseModifierFlags(mods)
        try MacosUseSDK.dragMouse(from: start, to: end, steps: steps, flags: flags)
        finish(success: true, message: "drag simulated from (\(start.x), \(start.y)) to (\(end.x), \(end.y)).")

    case "writetext":
         guard arguments.count == 3 else {
            throw MacosUseSDKError.inputInvalidArgument("'writetext' requires exactly one argument: <text_to_type>\n\(usage)")
        }
        let text = arguments[2]
        log("Text Argument: \"\(text)\"")
        log("Calling writeText library function...")
        try MacosUseSDK.writeText(text)
        finish(success: true, message: "Text writing simulated.")

    case "scroll":
        guard arguments.count >= 6 else {
            throw MacosUseSDKError.inputInvalidArgument("'scroll' requires <x> <y> <deltaY> <deltaX> [modifiers]")
        }
        let x = try requireDouble(arguments[2], label: "x")
        let y = try requireDouble(arguments[3], label: "y")
        guard let deltaY = Int32(arguments[4]), let deltaX = Int32(arguments[5]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid delta values for 'scroll'. deltaY and deltaX must be integers.")
        }
        let mods = arguments.count >= 7 ? arguments[6] : nil
        let flags = try parseModifierFlags(mods)
        let point = CGPoint(x: x, y: y)
        try MacosUseSDK.scrollWheel(at: point, deltaY: deltaY, deltaX: deltaX, flags: flags)
        finish(success: true, message: "Scroll simulated at (\(x), \(y)) with deltaY: \(deltaY), deltaX: \(deltaX).")

    case "cursorpos":
        let loc = MacosUseSDK.currentMouseLocation()
        print("\(loc.x) \(loc.y)")
        finish(success: true, message: "cursor at (\(loc.x), \(loc.y))")

    default:
        fputs(usage, stderr)
        throw MacosUseSDKError.inputInvalidArgument("Unknown action '\(action)'")
    }

} catch let error as MacosUseSDKError {
    // Handle specific SDK errors
    finish(success: false, message: "MacosUseSDK Error: \(error.localizedDescription)")
} catch {
    // Handle other unexpected errors
     finish(success: false, message: "An unexpected error occurred: \(error.localizedDescription)")
}

// Should not be reached due to finish() calls, but satisfies the compiler
exit(0)

/*
# Example: Open Calculator and type 2*3=
swift run AppOpenerTool Calculator
# (Wait a moment or use the PID from above if needed)
swift run InputControllerTool writetext "2*3="
*/
