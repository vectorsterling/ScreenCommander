import Foundation
import CoreAudio
import IOKit
import IOKit.graphics
import CoreGraphics

/// Errors that can occur when adjusting output settings
public enum OutputControllerError: Error, LocalizedError {
    case volumeAdjustmentFailed
    case brightnessAdjustmentFailed
    case volumeQueryFailed
    case brightnessQueryFailed
    case notSupported

    public var errorDescription: String? {
        switch self {
        case .volumeAdjustmentFailed:
            return "Failed to adjust system volume."
        case .brightnessAdjustmentFailed:
            return "Failed to adjust display brightness."
        case .volumeQueryFailed:
            return "Failed to query system volume."
        case .brightnessQueryFailed:
            return "Failed to query display brightness."
        case .notSupported:
            return "Operation not supported on this device."
        }
    }
}

/// Controller for adjusting system output settings (volume, brightness)
public enum OutputController {
    // MARK: - Volume

    /// Set the system output volume (0.0 - 1.0)
    @MainActor
    public static func setSystemVolume(_ volume: Float) throws {
        var defaultOutputDeviceID = AudioDeviceID(0)
        var propertyAddress = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDefaultOutputDevice,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var dataSize = UInt32(MemoryLayout<AudioDeviceID>.size)
        let status = AudioObjectGetPropertyData(
            AudioObjectID(kAudioObjectSystemObject),
            &propertyAddress,
            0,
            nil,
            &dataSize,
            &defaultOutputDeviceID
        )
        guard status == noErr else { throw OutputControllerError.volumeAdjustmentFailed }

        var volumeValue = volume
        propertyAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVolumeScalar,
            mScope: kAudioDevicePropertyScopeOutput,
            mElement: 0
        )
        let setStatus = AudioObjectSetPropertyData(
            defaultOutputDeviceID,
            &propertyAddress,
            0,
            nil,
            UInt32(MemoryLayout<Float32>.size),
            &volumeValue
        )
        guard setStatus == noErr else { throw OutputControllerError.volumeAdjustmentFailed }
    }

    /// Get the system output volume (0.0 - 1.0)
    @MainActor
    public static func getSystemVolume() throws -> Float {
        var defaultOutputDeviceID = AudioDeviceID(0)
        var propertyAddress = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDefaultOutputDevice,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var dataSize = UInt32(MemoryLayout<AudioDeviceID>.size)
        let status = AudioObjectGetPropertyData(
            AudioObjectID(kAudioObjectSystemObject),
            &propertyAddress,
            0,
            nil,
            &dataSize,
            &defaultOutputDeviceID
        )
        guard status == noErr else { throw OutputControllerError.volumeQueryFailed }

        var volume: Float32 = 0
        propertyAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVolumeScalar,
            mScope: kAudioDevicePropertyScopeOutput,
            mElement: 0
        )
        dataSize = UInt32(MemoryLayout<Float32>.size)
        let getStatus = AudioObjectGetPropertyData(
            defaultOutputDeviceID,
            &propertyAddress,
            0,
            nil,
            &dataSize,
            &volume
        )
        guard getStatus == noErr else { throw OutputControllerError.volumeQueryFailed }
        return volume
    }

    // MARK: - Brightness

    /// Set the main display brightness (0.0 - 1.0)
    @MainActor
    public static func setMainDisplayBrightness(_ brightness: Float) throws {
        guard let service = getIODisplayServicePort() else {
            throw OutputControllerError.notSupported
        }
        let result = IODisplaySetFloatParameter(service, 0, kIODisplayBrightnessKey as CFString, brightness)
        IOObjectRelease(service)
        guard result == kIOReturnSuccess else {
            throw OutputControllerError.brightnessAdjustmentFailed
        }
    }

    /// Get the main display brightness (0.0 - 1.0)
    @MainActor
    public static func getMainDisplayBrightness() throws -> Float {
        guard let service = getIODisplayServicePort() else {
            throw OutputControllerError.notSupported
        }
        var brightness: Float = 0
        let result = IODisplayGetFloatParameter(service, 0, kIODisplayBrightnessKey as CFString, &brightness)
        IOObjectRelease(service)
        guard result == kIOReturnSuccess else {
            throw OutputControllerError.brightnessQueryFailed
        }
        return brightness
    }

    // MARK: - Private Helpers

    /// Get the IODisplay service port for the main display
    private static func getIODisplayServicePort() -> io_service_t? {
        let displayID = CGMainDisplayID()
        var iter: io_iterator_t = 0
        let matching = IOServiceMatching("IODisplayConnect")
        let kernResult = IOServiceGetMatchingServices(kIOMainPortDefault, matching, &iter)
        if kernResult != KERN_SUCCESS {
            return nil
        }
        var service: io_service_t? = nil
        while case let serv = IOIteratorNext(iter), serv != 0 {
            let info = IODisplayCreateInfoDictionary(serv, IOOptionBits(kIODisplayOnlyPreferredName)).takeRetainedValue() as NSDictionary
            if let vendorID = info[kDisplayVendorID] as? UInt32,
               let productID = info[kDisplayProductID] as? UInt32 {
                if vendorID == CGDisplayVendorNumber(displayID) && productID == CGDisplayModelNumber(displayID) {
                    service = serv
                    break
                }
            }
            IOObjectRelease(serv)
        }
        IOObjectRelease(iter)
        return service
    }
}

// MARK: - C Constants for Display Info
private let kDisplayVendorID = "DisplayVendorID"
private let kDisplayProductID = "DisplayProductID"

public enum OutputControllerAction: String, Codable {
    case setVolume = "set-volume"
    case getVolume = "get-volume"
    case setBrightness = "set-brightness"
    case getBrightness = "get-brightness"
}

public struct OutputControllerResult: Codable {
    public let value: Float?
    public let message: String
}

@MainActor
public func outputControllerTool(
    action: OutputControllerAction,
    value: Float? = nil
) throws -> OutputControllerResult {
    switch action {
    case .setVolume:
        guard let v = value, v >= 0.0, v <= 1.0 else {
            throw OutputControllerError.volumeAdjustmentFailed
        }
        try OutputController.setSystemVolume(v)
        return OutputControllerResult(value: v, message: "System volume set to \(v)")
    case .getVolume:
        let v = try OutputController.getSystemVolume()
        return OutputControllerResult(value: v, message: "System volume is \(v)")
    case .setBrightness:
        guard let v = value, v >= 0.0, v <= 1.0 else {
            throw OutputControllerError.brightnessAdjustmentFailed
        }
        try OutputController.setMainDisplayBrightness(v)
        return OutputControllerResult(value: v, message: "Main display brightness set to \(v)")
    case .getBrightness:
        let v = try OutputController.getMainDisplayBrightness()
        return OutputControllerResult(value: v, message: "Main display brightness is \(v)")
    }
} 