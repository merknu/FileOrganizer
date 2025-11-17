# Changelog

All notable changes to FileOrganizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.007] - 2025-11-17

### Added
- **Custom Scenario Creator Dialog**: Create and save custom file organization workflows
  - Visual workflow builder with checkboxes for scan, analyze, organize, transfer, and cleanup steps
  - Path configuration with browse dialogs
  - Persistent storage as JSON files in user's config directory
  - Custom icons and descriptions support

- **Settings Dialog**: Comprehensive application settings
  - General settings (startup messages, tray behavior, exit confirmation)
  - Notification preferences (duration, completion/error toggles)
  - File organization options (auto-organize, verification, intervals)
  - Reset to defaults functionality
  - Persistent settings using Qt QSettings

- **File Organization Features**:
  - Individual file organization with error handling
  - Folder organization with recursive option
  - Downloads folder organization with dry-run preview
  - Desktop organization with platform detection

- **System Tray Enhancements**:
  - Quick organize feature from system tray
  - Full integration with file organization utilities

- **Scenario Execution Implementation**:
  - File scanning (recursive and non-recursive)
  - File analysis with duplicate detection
  - File transfer between locations
  - Video transcoding integration
  - Cleanup operations (temp files, old files, empty directories)

### Changed
- Replaced DEBUG print statements with proper logging in downloads_organizer.py
- Improved exception handling with specific exception types instead of bare except clauses
- Updated version to 0.2.007

### Fixed
- Better error handling in file time checking (OSError, ValueError, OverflowError)
- Input validation for custom scenarios
- Proper path handling with pathlib.Path objects

### Improved
- Code quality with consistent logging practices
- Documentation and docstrings for new features
- Settings persistence across sessions

## [0.2.006] - 2025-11-17

### Added
- Downloads folder scanning to find all files
- Comprehensive file move verification system

### Fixed
- File scanning now correctly identifies all files in downloads folder

## Previous Versions

See git history for earlier changes.
