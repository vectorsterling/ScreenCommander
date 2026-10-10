// The Swift Programming Language
// https://docs.swift.org/swift-book

import Foundation
import UniformTypeIdentifiers  // Required for UTType

/// Response structure for file search results
public struct FileSearchResult: Codable, Sendable {
    public var files: [FileInfo]
    public var totalCount: Int
    public var executionTime: String
    
    public init(files: [FileInfo], totalCount: Int, executionTime: String) {
        self.files = files
        self.totalCount = totalCount
        self.executionTime = executionTime
    }
}

/// Structure to represent file information
public struct FileInfo: Codable, Sendable, Hashable {
    public var path: String
    public var name: String
    public var size: Int64
    public var creationDate: Date?
    public var modificationDate: Date?
    public var fileType: String
    
    public init(path: String, name: String, size: Int64, creationDate: Date?, modificationDate: Date?, fileType: String) {
        self.path = path
        self.name = name
        self.size = size
        self.creationDate = creationDate
        self.modificationDate = modificationDate
        self.fileType = fileType
    }
}

/// Options for file search
public struct FileSearchOptions: Codable, Sendable {
    public var fileName: String?
    public var fileType: String?
    public var startDate: Date?
    public var endDate: Date?
    public var searchLocations: [String]
    public var maxResults: Int
    
    public init(fileName: String? = nil, 
                fileType: String? = nil, 
                startDate: Date? = nil, 
                endDate: Date? = nil, 
                searchLocations: [String] = [NSHomeDirectory()], 
                maxResults: Int = 100) {
        self.fileName = fileName
        self.fileType = fileType
        self.startDate = startDate
        self.endDate = endDate
        self.searchLocations = searchLocations.isEmpty ? [NSHomeDirectory()] : searchLocations
        self.maxResults = maxResults > 0 ? maxResults : 100
    }
}

/// File search errors
public enum FileSearchError: Error, LocalizedError {
    case invalidSearchCriteria
    case searchFailed(String)
    
    public var errorDescription: String? {
        switch self {
        case .invalidSearchCriteria:
            return "Invalid search criteria. Please provide at least a file name, file type, or date range."
        case .searchFailed(let message):
            return "File search failed: \(message)"
        }
    }
}

/// Search for files based on the given criteria
/// - Parameter options: The search options
/// - Returns: FileSearchResult containing the matched files
/// - Throws: FileSearchError if the search fails
public func searchFiles(options: FileSearchOptions) async throws -> FileSearchResult {
    let startTime = Date()
    fputs("info: starting file search with options: \(options)\n", stderr)
    
    // Validate search criteria
    if options.fileName == nil && options.fileType == nil && options.startDate == nil && options.endDate == nil {
        throw FileSearchError.invalidSearchCriteria
    }
    
    var allFiles = [FileInfo]()
    var totalCount = 0
    
    // Process each search location
    for location in options.searchLocations {
        fputs("info: searching in location: \(location)\n", stderr)
        
        do {
            let files = try await searchInLocation(
                location: location,
                fileName: options.fileName,
                fileType: options.fileType,
                startDate: options.startDate,
                endDate: options.endDate,
                maxResults: options.maxResults - allFiles.count
            )
            
            allFiles.append(contentsOf: files)
            totalCount += files.count
            
            // Stop if we've reached the maximum number of results
            if allFiles.count >= options.maxResults {
                fputs("info: reached maximum result count (\(options.maxResults))\n", stderr)
                break
            }
        } catch {
            fputs("warning: error searching location \(location): \(error.localizedDescription)\n", stderr)
        }
    }
    
    let endTime = Date()
    let executionTime = String(format: "%.3f", endTime.timeIntervalSince(startTime))
    fputs("info: file search completed in \(executionTime) seconds. Found \(allFiles.count) files.\n", stderr)
    
    return FileSearchResult(
        files: allFiles,
        totalCount: totalCount,
        executionTime: executionTime
    )
}

/// Search for files in a specific location using FileManager
private func searchInLocation(location: String,
                            fileName: String?,
                            fileType: String?,
                            startDate: Date?,
                            endDate: Date?,
                            maxResults: Int) async throws -> [FileInfo] {
    // FileManager enumeration must not use Sequence iteration from async contexts (Swift 6+).
    return await Task.detached(priority: .userInitiated) {
        searchInLocationSync(
            location: location,
            fileName: fileName,
            fileType: fileType,
            startDate: startDate,
            endDate: endDate,
            maxResults: maxResults
        )
    }.value
}

private func searchInLocationSync(location: String,
                                  fileName: String?,
                                  fileType: String?,
                                  startDate: Date?,
                                  endDate: Date?,
                                  maxResults: Int) -> [FileInfo] {
    let fileManager = FileManager.default
    var results = [FileInfo]()

    guard fileManager.fileExists(atPath: location) else {
        fputs("warning: location does not exist or cannot be accessed: \(location)\n", stderr)
        return results
    }

    let url = URL(fileURLWithPath: location).standardized
    let resourceKeys: [URLResourceKey] = [
        .nameKey, .fileSizeKey, .contentTypeKey,
        .creationDateKey, .contentModificationDateKey,
    ]
    let options: FileManager.DirectoryEnumerationOptions = [.skipsHiddenFiles, .skipsPackageDescendants]

    guard let enumerator = fileManager.enumerator(
        at: url,
        includingPropertiesForKeys: resourceKeys,
        options: options
    ) else {
        fputs("warning: could not create file enumerator for: \(location)\n", stderr)
        return results
    }

    var processedCount = 0
    let startEnumeration = Date()

    while let object = enumerator.nextObject() {
        guard let fileURL = object as? URL else { continue }

        processedCount += 1
        if processedCount % 1000 == 0 {
            let elapsed = Date().timeIntervalSince(startEnumeration)
            fputs(
                "info: processed \(processedCount) files in \(location) (\(String(format: "%.1f", elapsed))s) - found \(results.count) matches so far\n",
                stderr
            )
        }

        do {
            let resourceValues = try fileURL.resourceValues(forKeys: Set(resourceKeys))
            let name = fileURL.lastPathComponent
            let path = fileURL.path

            if let filePattern = fileName, !name.localizedCaseInsensitiveContains(filePattern) {
                continue
            }

            if let typePattern = fileType,
               let contentType = resourceValues.contentType?.identifier,
               contentType != typePattern,
               !contentTypeConformsToSync(contentType: contentType, parentType: typePattern) {
                continue
            }

            let modDate = resourceValues.contentModificationDate
            if let start = startDate, let fileDate = modDate, fileDate < start {
                continue
            }
            if let end = endDate, let fileDate = modDate, fileDate > end {
                continue
            }

            let fileInfo = FileInfo(
                path: path,
                name: name,
                size: Int64(resourceValues.fileSize ?? 0),
                creationDate: resourceValues.creationDate,
                modificationDate: modDate,
                fileType: resourceValues.contentType?.identifier ?? "unknown"
            )
            results.append(fileInfo)

            if results.count >= maxResults {
                fputs("info: reached maximum result count for location (\(maxResults))\n", stderr)
                break
            }
        } catch {
            continue
        }
    }

    fputs(
        "info: search in \(location) completed. Found \(results.count) matching files (processed \(processedCount) total).\n",
        stderr
    )
    return results
}

/// Check if a content type conforms to another content type (e.g., if JPEG is a type of Image)
private func contentTypeConformsToSync(contentType: String, parentType: String) -> Bool {
    if contentType == parentType {
        return true
    }
    if let type = UTType(contentType),
       let parentUTType = UTType(parentType) {
        return type.conforms(to: parentUTType)
    }
    return false
} 