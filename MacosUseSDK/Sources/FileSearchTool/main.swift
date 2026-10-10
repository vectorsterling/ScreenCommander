// main.swift for FileSearchTool
// Command-line tool to search for files on macOS with various criteria

import Foundation
import MacosUseFileSearch

// Use @main struct for async top-level code
@main
struct FileSearchTool {
    
    static func main() async {
        fputs("info: FileSearchTool started\n", stderr)
        
        // --- Argument Parsing ---
        let arguments = CommandLine.arguments
        
        // Ensure we have at least one argument
        guard arguments.count > 1 else {
            printUsage()
            exit(1)
        }
        
        // Parse arguments
        var fileName: String?
        var fileType: String?
        var startDateStr: String?
        var endDateStr: String?
        var searchLocations: [String] = []
        var maxResults = 100
        
        var i = 1
        while i < arguments.count {
            let arg = arguments[i]
            
            switch arg {
            case "--help", "-h":
                printUsage()
                exit(0)
                
            case "--name", "-n":
                if i + 1 < arguments.count {
                    fileName = arguments[i + 1]
                    i += 2
                } else {
                    fputs("error: missing value for --name parameter\n", stderr)
                    exit(1)
                }
                
            case "--type", "-t":
                if i + 1 < arguments.count {
                    fileType = arguments[i + 1]
                    i += 2
                } else {
                    fputs("error: missing value for --type parameter\n", stderr)
                    exit(1)
                }
                
            case "--start-date", "-s":
                if i + 1 < arguments.count {
                    startDateStr = arguments[i + 1]
                    i += 2
                } else {
                    fputs("error: missing value for --start-date parameter\n", stderr)
                    exit(1)
                }
                
            case "--end-date", "-e":
                if i + 1 < arguments.count {
                    endDateStr = arguments[i + 1]
                    i += 2
                } else {
                    fputs("error: missing value for --end-date parameter\n", stderr)
                    exit(1)
                }
                
            case "--location", "-l":
                if i + 1 < arguments.count {
                    searchLocations.append(arguments[i + 1])
                    i += 2
                } else {
                    fputs("error: missing value for --location parameter\n", stderr)
                    exit(1)
                }
                
            case "--max", "-m":
                if i + 1 < arguments.count, let value = Int(arguments[i + 1]) {
                    maxResults = value
                    i += 2
                } else {
                    fputs("error: missing or invalid value for --max parameter\n", stderr)
                    exit(1)
                }
                
            default:
                // If not recognized, assume it's a plain search term for filename
                if fileName == nil {
                    fileName = arg
                }
                i += 1
            }
        }
        
        // Parse dates
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        
        var startDate: Date?
        if let startDateStr = startDateStr {
            startDate = dateFormatter.date(from: startDateStr)
            if startDate == nil {
                fputs("error: invalid start date format. Please use YYYY-MM-DD\n", stderr)
                exit(1)
            }
        }
        
        var endDate: Date?
        if let endDateStr = endDateStr {
            endDate = dateFormatter.date(from: endDateStr)
            if endDate == nil {
                fputs("error: invalid end date format. Please use YYYY-MM-DD\n", stderr)
                exit(1)
            }
            
            // Make end date inclusive by setting it to the end of the day
            if let date = endDate {
                endDate = Calendar.current.date(bySettingHour: 23, minute: 59, second: 59, of: date)
            }
        }
        
        // Default search location to user's home directory if not specified
        if searchLocations.isEmpty {
            searchLocations.append(NSHomeDirectory())
        }
        
        // Create search options
        let options = FileSearchOptions(
            fileName: fileName,
            fileType: fileType,
            startDate: startDate,
            endDate: endDate,
            searchLocations: searchLocations,
            maxResults: maxResults
        )
        
        // Log search parameters
        fputs("info: searching with the following parameters:\n", stderr)
        fputs("  - File name: \(fileName ?? "any")\n", stderr)
        fputs("  - File type: \(fileType ?? "any")\n", stderr)
        fputs("  - Start date: \(startDateStr ?? "any")\n", stderr)
        fputs("  - End date: \(endDateStr ?? "any")\n", stderr)
        fputs("  - Locations: \(searchLocations.joined(separator: ", "))\n", stderr)
        fputs("  - Max results: \(maxResults)\n", stderr)
        
        // Perform search
        do {
            let result = try await searchFiles(options: options)
            
            // Convert to JSON
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            
            let jsonData = try encoder.encode(result)
            
            // Output JSON to stdout
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                print(jsonString)
                fputs("info: found \(result.files.count) files in \(result.executionTime) seconds\n", stderr)
                exit(0) // Success
            } else {
                fputs("error: failed to convert result to JSON string\n", stderr)
                exit(1)
            }
        } catch let error as FileSearchError {
            fputs("❌ FileSearchError: \(error.localizedDescription)\n", stderr)
            exit(1)
        } catch {
            fputs("❌ An unexpected error occurred: \(error.localizedDescription)\n", stderr)
            exit(1)
        }
    }
    
    static func printUsage() {
        let executableName = URL(fileURLWithPath: CommandLine.arguments[0]).lastPathComponent
        
        fputs("""
        Usage: \(executableName) [options] [search_term]
        
        Options:
          --name, -n <name>          File name or pattern to search for
          --type, -t <type>          File type/UTI (e.g., public.image, public.pdf)
          --start-date, -s <date>    Start date in YYYY-MM-DD format
          --end-date, -e <date>      End date in YYYY-MM-DD format
          --location, -l <path>      Directory to search in (can be specified multiple times)
          --max, -m <number>         Maximum number of results (default: 100)
          --help, -h                 Show this help message
        
        Examples:
          \(executableName) --name report.pdf
          \(executableName) --type public.image --start-date 2023-01-01
          \(executableName) report --location ~/Documents --location ~/Downloads
        
        Notes:
          - If no search location is specified, searches in the user's home directory
          - At least one search criterion (name, type, or date range) is required
          - Common file type UTIs:
            - public.image       : All image types
            - public.jpeg        : JPEG images
            - public.png         : PNG images
            - public.pdf         : PDF documents
            - public.text        : Text files
            - public.audio       : Audio files
            - public.video       : Video files
            - public.archive     : Archive files
            - com.apple.keynote.key : Keynote presentations
            - com.microsoft.word.doc : Word documents
            - com.microsoft.excel.xls : Excel spreadsheets
        
        """, stderr)
    }
}

/*
# Example: Search for PDF files with "report" in the name
swift run FileSearchTool --name report --type public.pdf

# Example: Search for images modified since January 1, 2023
swift run FileSearchTool --type public.image --start-date 2023-01-01

# Example: Search in multiple locations
swift run FileSearchTool report --location ~/Documents --location ~/Downloads
*/ 