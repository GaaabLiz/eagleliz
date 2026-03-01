# Eagleliz - AI Context and Documentation

Welcome to the `eagleliz` project! This file provides essential context about the repository for AI assistants (like Antigravity / Claude / Copilot).

## 🎯 Purpose
`eagleliz` is a collection of Python-based utility CLI scripts aimed at interacting with the [Eagle.cool API](https://api.eagle.cool) and managing media files (images, videos). Its primary goals represent a specific workflow for organizing media or generating XMP sidecar metadata files seamlessly.

## 🏗️ Architecture & Project Structure
The project uses `typer` for its command-line interface and heavily relies on `pylizlib` (a shared custom library) for media handling and core application setup.

- `pyproject.toml` / `uv.lock`: Project uses `uv` for dependency management. Support Python >= 3.12.
- `makefile` / `project.mk`: Utilities for building, linting, or formatting.
- `eagleliz/`: Main package directory.
  - `cli.py`: The main entry point `eagleliz_app()`. Sets up the `PylizApp` and root file logger.
  - `organizer.py`: The `organizer` CLI command. Copies and organizes files from a source to an output location, filtering by Eagle tags or regex, and can generate `.xmp` metadata sidecars automatically.
  - `sidegen.py`: The `sidegen` CLI command. Searches an existing Eagle Catalog and creates or updates `.xmp` sidecar files in-place alongside the media elements.
  - `domain.py`: Core dataclasses (e.g., `OrganizerOptions`, `OrganizerResult`) functioning as Data Transfer Objects representing execution options and file states.
  - `controller/`: Business logic implementations.
    - `media_org.py`: Implements `MediaOrganizer` that performs the actual physical copying and organization.
    - `searcher.py`, `searcher_eagle.py`, `searcher_os.py`: Gather and iterate through files either via the file system or Eagle's local metadata structures.
  - `model/`: Defines data models.
    - `metadata.py`: Eagle layout and sidecar metadata abstractions.

## 🛠️ Key Technologies
- **Python >= 3.12**
- **Dependency Management**: `uv` (recommended over pip standard)
- **CLI Framework**: `typer` + `rich` (for gorgeous terminal UIs) + `tqdm` (for progress bars)
- **Base Library**: `pylizlib[media]` (provides `LizMedia`, `MetadataHandler`, `PylizApp`)

## 📜 Conventions & Guidelines for AI
1. **Adding CLI Commands**: Any new CLI script should be integrated into `eagleliz_app` (defined via `pylizlib` standard `typer` instantiation) and follow the pattern established by `organizer` and `sidegen`.
2. **Error Handling & Logs**: `cli.py` is configured to log to a file (inside the `PylizDirFoldersTemplate.LOGS` directory). Console output for users should generally utilize `rich` `print` or `typer.echo`. Avoid polluting the console with Python native debug print statements.
3. **Immutability & Domain Models**: When making changes to the data being passed across the controller, respect the dataclasses defined in `domain.py`. 
4. **Build & Test**: Always check `makefile` for testing / formatting rules before finalizing code modifications. Use `uv run` if executing tests locally instead of direct `pytest`.
5. **Eagle Context**: Understand that Eagle references refer specifically to the `eagle.cool` desktop application for designers and media handling, referencing `.eagle` libraries metadata structures or local files.
