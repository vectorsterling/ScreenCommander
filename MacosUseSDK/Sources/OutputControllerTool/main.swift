import Foundation
import MacosUseSDK

let startTime = Date()

func log(_ message: String) {
    fputs("OutputControllerTool: \(message)\n", stderr)
}

func finish(success: Bool, message: String? = nil) -> Never {
    if let msg = message {
        log(success ? "✅ Success: \(msg)" : "❌ Error: \(msg)")
    }
    let endTime = Date()
    let processingTime = endTime.timeIntervalSince(startTime)
    let formattedTime = String(format: "%.3f", processingTime)
    fputs("OutputControllerTool: total execution time: \(formattedTime) seconds\n", stderr)
    exit(success ? 0 : 1)
}

let arguments = CommandLine.arguments
let scriptName = arguments.first ?? "OutputControllerTool"

let usage = """
usage: \(scriptName) <action> [value]

actions:
  set-volume <value>      Set system output volume (0.0 - 1.0)
  get-volume              Get system output volume
  set-brightness <value>  Set main display brightness (0.0 - 1.0)
  get-brightness          Get main display brightness

Examples:
  \(scriptName) set-volume 0.5
  \(scriptName) get-volume
  \(scriptName) set-brightness 0.8
  \(scriptName) get-brightness
"""

guard arguments.count > 1 else {
    fputs(usage, stderr)
    finish(success: false, message: "No action specified.")
}

let action = arguments[1].lowercased()
log("Action: \(action)")

do {
    let result: OutputControllerResult
    switch action {
    case "set-volume":
        guard arguments.count == 3, let value = Float(arguments[2]) else {
            throw OutputControllerError.volumeAdjustmentFailed
        }
        result = try MacosUseSDK.outputControllerTool(action: .setVolume, value: value)
        print(result.value ?? "")
        finish(success: true, message: result.message)
    case "get-volume":
        result = try MacosUseSDK.outputControllerTool(action: .getVolume)
        print(result.value ?? "")
        finish(success: true, message: result.message)
    case "set-brightness":
        guard arguments.count == 3, let value = Float(arguments[2]) else {
            throw OutputControllerError.brightnessAdjustmentFailed
        }
        result = try MacosUseSDK.outputControllerTool(action: .setBrightness, value: value)
        print(result.value ?? "")
        finish(success: true, message: result.message)
    case "get-brightness":
        result = try MacosUseSDK.outputControllerTool(action: .getBrightness)
        print(result.value ?? "")
        finish(success: true, message: result.message)
    default:
        fputs(usage, stderr)
        finish(success: false, message: "Unknown action '\(action)'")
    }
} catch let error as OutputControllerError {
    finish(success: false, message: error.localizedDescription)
} catch {
    finish(success: false, message: "An unexpected error occurred: \(error.localizedDescription)")
}

exit(0) 