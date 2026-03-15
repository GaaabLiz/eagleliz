## [0.0.20] - 2026-03-15

### 🚀 Features

- Introduce AI context documentation and an onboarding workflow for the project.
- Implement Eagle.cool API client with application info and folder management, along with initial tests.
- Add folder update, list, and item add from URL API methods with corresponding tests.
- Add `EagleItemURLPayload` dataclass and `add_items_from_urls` method with a corresponding test.
- Implement `add_item_from_path` API method and add its integration test.
- Implement batch adding of local items via `add_items_from_paths` API and add corresponding test.
- Add `add_bookmark` method to the API client and include a corresponding test case.
- Implement item info retrieval with `EagleItem` dataclass for robust data handling and add a negative test case.
- Add `get_item_thumbnail` method to the API and include a corresponding test case.
- Add `get_items` method with filtering/sorting and update item info/thumbnail tests to use retrieved item IDs.
- Add `move_to_trash` API method and a corresponding test case for moving items to trash.
- Add API methods for refreshing item palette and thumbnail, and include corresponding tests.
- Implement `update_item` API method and add `star` field to `EagleItem` model.
- Add `LibraryInfo` dataclass, `get_library_info`, and `get_library_history` methods to `EagleAPI` with corresponding tests.
- Add methods to switch libraries and retrieve library icons with corresponding tests.
- Add Immich integration, remove old API files, and update .gitignore.
- Add Immich integration module.
- Add initial TestCatalog.library files and update .gitignore.
- Populate TestCatalog.library with new assets and metadata, and refactor test files.
- Add Immich integration with an API client for uploading and updating assets, introducing `python-dotenv` and `requests` dependencies.
- Added async api client and token support

### 💼 Other

- Bump version to 0.0.20

### 🚜 Refactor

- Reorganize imports and rename domain.py to organizer.py
- Modularize project structure by creating new packages and removing old test library files. Added documentation to all eagleliz files.

### ⚙️ Miscellaneous Tasks

- Update changelog [skip ci]
## [0.0.19] - 2026-02-28

### 🚀 Features

- Add logol.ico
- Add base64 content handling to EagleCoolReader

### 💼 Other

- Bump version to 0.0.19

### ⚙️ Miscellaneous Tasks

- Update changelog [skip ci]
## [0.0.18] - 2026-02-28

### 🚀 Features

- Add metadata handling and reader classes for Eagle library

### 💼 Other

- Bump version to 0.0.18

### ⚙️ Miscellaneous Tasks

- Update changelog [skip ci]
## [0.0.17] - 2026-02-28

### 💼 Other

- Bump version to 0.0.13
- Update version to 0.0.15
- Bump version to 0.0.16
- Update version to 0.0.15
- Bump version to 0.0.17

### ⚙️ Miscellaneous Tasks

- Rename old module files and update import paths
- Update changelog [skip ci]
## [0.0.11] - 2026-02-28

### 💼 Other

- Bump version to 0.0.11

### ⚙️ Miscellaneous Tasks

- Update changelog [skip ci]
## [0.0.9] - 2026-02-28

### 🚀 Features

- Refactor entry point to use main function and bump version to 0.0.8

### 💼 Other

- Bump version to 0.0.9

### ⚙️ Miscellaneous Tasks

- Update changelog [skip ci]
## [0.0.7] - 2026-02-28

### 🚀 Features

- Add project metadata including name, version, description, and author information
- Update makefile with platform detection and enhanced build commands

### 💼 Other

- Bump version to 0.0.7
## [0.0.6] - 2026-02-28

### 🚀 Features

- Add to_xmp method for XML metadata serialization
- Implement eagle2xmp command for generating XMP sidecar files from Eagle.cool metadata
- Enhance metadata model with optional fields and improve XMP serialization
- Add eagleliz command for CLI application entry point
- Refactor CLI application and add export organized workflow command. Moved old code into separate package
- Created media_reader.py and refactored exporg.py
- Re-added setup.py
- Re-added setup.py
- Refactored project
- Refactored project
- Reorganized project structure and updated imports
- Add eagleliz command line utility with Typer integration
- Add search strategies for Eagle library and filesystem
- Implement core media organization logic with file handling and conflict resolution
- Add domain models for media organization with configuration options
- Add MediaSearcher class for media file search strategies and XMP generation
- Add CLI module with logging setup for eagleliz application
- Add sidegen command for generating XMP sidecar files in Eagle catalog
- Add organizer command for media file organization in pylizmedia CLI
- Update project configuration and add release workflow for PyPI

### 💼 Other

- Bump version to 0.0.6

### ⚙️ Miscellaneous Tasks

- Add pyproject.toml and uv.lock for project dependencies
