# eagleliz

![Python >=3.12](https://img.shields.io/badge/python-%3E%3D3.12-blue)
![CLI Typer](https://img.shields.io/badge/CLI-Typer-009688)
![HTTP API Eagle.cool](https://img.shields.io/badge/Eagle.cool-local%20API-6C63FF)

Python utilities and API bindings for automating [Eagle.cool](https://eagle.cool) libraries, media organization workflows, and XMP sidecar generation.

## Overview

`eagleliz` is an open-source Python package for people who work with local Eagle libraries and want to automate repetitive media-management tasks.

The repository combines two complementary layers:

- a **typed Python client** for Eagle's local HTTP API, with both synchronous and asynchronous implementations;
- a **CLI toolkit** for scanning media files, reading Eagle `.library` catalogs directly from disk, generating XMP sidecars, and organizing files into date-based folders.

The project is especially useful if you:

- automate Eagle from Python scripts or local tools;
- maintain a media workflow involving images, videos, audio, text, bookmarks, or sidecar files;
- want to preserve Eagle tags/annotations while generating XMP metadata;
- need to reorganize or export media from an Eagle catalog into a filesystem-friendly structure.

## Table of Contents

- [Features](#features)
- [Requirements and Dependencies](#requirements-and-dependencies)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Usage](#usage)
  - [Use the synchronous Eagle API client](#use-the-synchronous-eagle-api-client)
  - [Import local files into Eagle](#import-local-files-into-eagle)
  - [Use the asynchronous client](#use-the-asynchronous-client)
  - [Upload a local image through the extended async helper](#upload-a-local-image-through-the-extended-async-helper)
  - [Run the organizer CLI](#run-the-organizer-cli)
  - [Generate XMP sidecars from an Eagle catalog](#generate-xmp-sidecars-from-an-eagle-catalog)
- [Configuration](#configuration)
- [API at a Glance](#api-at-a-glance)
- [Best Practices](#best-practices)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Support and Contact](#support-and-contact)
- [License](#license)
- [Credits](#credits)

## Features

- Typed **sync and async clients** for the local Eagle HTTP API.
- Dataclass-based API models for:
  - application info,
  - library info,
  - folders,
  - items,
  - batch payloads.
- Support for core Eagle workflows such as:
  - reading application and library metadata,
  - creating, renaming, updating, and listing folders,
  - adding items from URLs,
  - batch-adding items from URLs or local paths,
  - adding bookmarks,
  - reading item info and thumbnails,
  - updating tags, annotations, URL, and star rating,
  - refreshing thumbnails and palette data,
  - moving items to trash.
- `AsynchEagleApiExtended` helper for uploading a **local image file** by converting it to a base64 data URI and sending it through `POST /api/item/addFromURL`.
- `organizer` CLI command to:
  - scan a normal filesystem directory, or
  - read an Eagle `.library` catalog,
  - preview accepted/rejected/errored files,
  - optionally generate missing XMP sidecars,
  - copy media and attached sidecars into an `output/YYYY/MM` structure.
- `sidegen` CLI command to create or recreate `.xmp` sidecars directly inside an Eagle catalog.
- Local catalog reader and searchers for working with Eagle libraries **without going through the HTTP API**.
- Secondary integration module for **Immich** uploads and asset metadata updates.

## Requirements and Dependencies

### Python

- **Python >= 3.12**

### Runtime dependencies

Declared in `pyproject.toml`:

- `pylizlib[media]>=0.3.70`
- `typer>=0.9.0`
- `rich>=13.0.0`
- `tqdm>=4.66.0`
- `requests>=2.32.5`
- `python-dotenv>=1.2.1`
- `httpx>=0.28.1`

### External tools and services

- **Eagle.cool desktop app** must be running for the HTTP API clients.
- The API clients default to the local Eagle endpoint:
  - `http://localhost:41595/api`
- XMP-related workflows rely on `pylizlib` metadata handling. The in-repo docs for `organizer` note that richer XMP generation depends on **`exiftool`** being available on `PATH`.

### Supported environments

The repository includes cross-platform development/build helpers in `makefile` for:

- macOS
- Linux
- Windows

`eagleliz` itself targets local Eagle workflows, so the practical runtime requirement is: **a system where Eagle.cool and Python 3.12+ are available**.

## Installation

### Install from PyPI

```bash
pip install eagleliz
```

### Install for local development with `uv`

```bash
uv sync
uv sync --group dev
```

### Editable install with `pip`

```bash
pip install -e .
```

### CLI entry point

The package exposes this console script:

```text
eagleliz = eagleliz.cli:main
```

After installation, you can inspect the CLI with:

```bash
eagleliz --help
```

## Quickstart

### Minimal Python example

The fastest way to confirm the package is wired correctly is to query the local Eagle app.

```python
from eagleliz.api import EagleAPI

client = EagleAPI()

app_info = client.get_application_info()
library_info = client.get_library_info()

print(f"Eagle version: {app_info.version}")
print(f"Platform: {app_info.platform}")
print(f"Folders in current library: {len(library_info.folders)}")
```

### Minimal CLI example

Preview how files would be organized, without writing anything:

```bash
eagleliz organizer /absolute/path/to/source /absolute/path/to/output --dry
```

This command:

- scans the source directory,
- prints accepted/rejected/errored tables,
- waits for confirmation,
- simulates the organization step,
- reports the expected output layout.

## Usage

### Use the synchronous Eagle API client

```python
from eagleliz.api import EagleAPI

client = EagleAPI()

info = client.get_application_info()
history = client.get_library_history()
folders = client.list_folders()

print(info.version)
print(history[0] if history else "No recent libraries")
print(f"Folder count: {len(folders)}")
```

You can also initialize a client from a full Eagle URL, including a token:

```python
from eagleliz.api import EagleAPI

client = EagleAPI.from_url("http://localhost:41595/api?token=YOUR_TOKEN")
print(client.get_application_info().version)
```

### Import local files into Eagle

This mirrors the patterns used by the test suite.

```python
from eagleliz.api import EagleAPI

client = EagleAPI()

folder = client.create_folder("Imported Assets")

client.add_item_from_path(
	path="/absolute/path/to/file.txt",
	name="Local note",
	tags=["LocalPath", "Example"],
	annotation="Imported from disk",
	folder_id=folder.id,
)

items = client.get_items(keyword="Local note", folders=[folder.id], limit=1)
print(items[0].id)
```

Batch creation is also supported:

```python
from eagleliz.api import EagleAPI, EagleItemPathPayload

client = EagleAPI()

payloads = [
	EagleItemPathPayload(path="/tmp/one.txt", name="BatchPath1", tags=["batch"]),
	EagleItemPathPayload(path="/tmp/two.txt", name="BatchPath2", tags=["batch"]),
]

client.add_items_from_paths(payloads)
```

### Use the asynchronous client

`AsyncEagleAPI` mirrors the public surface of `EagleAPI`, making it easier to switch between sync and async applications.

```python
import asyncio

from eagleliz.api import AsyncEagleAPI


async def main() -> None:
	client = AsyncEagleAPI()

	app_info = await client.get_application_info()
	library_info = await client.get_library_info()

	print(app_info.version)
	print(len(library_info.folders))


asyncio.run(main())
```

### Upload a local image through the extended async helper

`AsynchEagleApiExtended` adds a convenience method for uploading a local image file when you want Eagle to receive the file contents as a data URI.

```python
import asyncio

from eagleliz.api import AsynchEagleApiExtended


async def main() -> None:
	client = AsynchEagleApiExtended()

	item_id = await client.add_item_from_file(
		path="/absolute/path/to/image.png",
		name="Imported from file",
		tags=["local", "upload"],
	)

	print(item_id)


asyncio.run(main())
```

### Run the organizer CLI

Organize files from a regular directory into a date-based output tree:

```bash
eagleliz organizer /absolute/path/to/source /absolute/path/to/output
```

Preview only:

```bash
eagleliz organizer /absolute/path/to/source /absolute/path/to/output --dry
```

Exclude files by filename regex:

```bash
eagleliz organizer /absolute/path/to/source /absolute/path/to/output --dry --exclude 'exclude_me'
```

Read directly from an Eagle catalog and filter by tags:

```bash
eagleliz organizer /absolute/path/to/MyCatalog.library /absolute/path/to/output --eaglecatalog --dry --eagletag BatchURL
```

Generate missing XMP sidecars before the organization step:

```bash
eagleliz organizer /absolute/path/to/source /absolute/path/to/output --xmp
```

What the current CLI does, based on the code and tests:

- it is **interactive** and waits for `Enter` before the final organization step;
- it currently **copies** files rather than moving them;
- output is organized under `output/YYYY/MM`;
- sidecars attached to a media item are copied alongside the main file.

### Generate XMP sidecars from an Eagle catalog

Create or refresh `.xmp` sidecars next to media files inside an Eagle `.library` catalog:

```bash
eagleliz sidegen /absolute/path/to/MyCatalog.library
```

Preview only:

```bash
eagleliz sidegen /absolute/path/to/MyCatalog.library --dry
```

Filter by tag:

```bash
eagleliz sidegen /absolute/path/to/MyCatalog.library --dry --eagletag DynamicTest
```

The implementation recreates existing `.xmp` files in place when not running in dry-run mode.

## Configuration

### API configuration

#### `EAGLE_URL`

The shared client base class supports initialization from an environment variable:

```bash
export EAGLE_URL='http://localhost:41595/api?token=YOUR_TOKEN'
```

```python
from eagleliz.api import EagleAPI

client = EagleAPI.from_env()
```

If `EAGLE_URL` is not set, clients default to:

```text
http://localhost:41595/api
```

#### Immich integration

`eagleliz.integration.immich.ImmichAPI` reads these variables when constructor arguments are omitted:

- `IMMICH_URL`
- `IMMICH_API_KEY`

### CLI environment variables

The CLI exposes many options through environment variables.

#### `organizer`

- `PYL_M_ORG_PATH`
- `PYL_M_ORG_OUTPUT`
- `PYL_M_ORG_EAGLECATALOG`
- `PYL_M_ORG_EAGLETAG`
- `PYL_M_ORG_XMP`
- `PYL_M_ORG_DRY`
- `PYL_M_ORG_EXCLUDE`
- `PYL_M_ORG_LIST_ACCEPTED`
- `PYL_M_ORG_LIST_REJECTED`
- `PYL_M_ORG_LIST_ERRORED`
- `PYL_M_ORG_LIST_ACCEPTED_ORDER_INDEX`
- `PYL_M_ORG_LIST_REJECTED_ORDER_INDEX`
- `PYL_M_ORG_LIST_ERRORED_ORDER_INDEX`
- `PYL_M_ORG_PRINT_RESULTS`
- `PYL_M_ORG_LIST_RESULT_ORDER_INDEX`

Example:

```bash
export PYL_M_ORG_PATH='/absolute/path/to/source'
export PYL_M_ORG_OUTPUT='/absolute/path/to/output'
export PYL_M_ORG_DRY='1'

eagleliz organizer
```

#### `sidegen`

- `PYL_M_SIDEGEN_PATH`
- `PYL_M_SIDEGEN_EAGLETAG`
- `PYL_M_SIDEGEN_DRY`

## API at a Glance

### Main modules

- `eagleliz.api`
  Public entry point for sync/async Eagle API clients, shared exceptions, and typed models.
- `eagleliz.local.reader`
  Reads an Eagle `.library` bundle directly from disk and resolves media files plus `metadata.json` content.
- `eagleliz.local.searcher*`
  Search utilities for filesystem scanning, Eagle-catalog scanning, and result printing.
- `eagleliz.controller.media_org`
  Core file-organization logic for copying/moving media and attached sidecars.
- `eagleliz.integration.immich`
  Separate helper for uploading assets to Immich and updating asset metadata.

### Important classes and functions

- `EagleAPI`
  Synchronous client for the local Eagle HTTP API.
- `AsyncEagleAPI`
  Asynchronous `httpx`-based client exposing the same public API surface as the sync client.
- `AsynchEagleApiExtended`
  Async convenience wrapper that uploads local image files by converting them to base64 data URIs.
- `EagleAPIError`
  Unified exception type for transport failures, HTTP errors, invalid responses, and Eagle-side API errors.
- `ApplicationInfo`, `LibraryInfo`, `EagleFolder`, `EagleItem`
  Dataclass models returned by the typed API clients.
- `EagleItemURLPayload`, `EagleItemPathPayload`
  Batch payload objects for multi-item import operations.
- `EagleLocalReader`
  Direct catalog reader for `.library/images/*` entries and related `metadata.json` files.
- `EagleCatalogSearcher`
  Builds accepted/rejected/errored search results from a local Eagle catalog and links sidecar files.
- `FileSystemSearcher`
  Recursively scans a normal directory and accepts files recognized as media by `pylizlib`.
- `EagleLocalSearcher`
  Facade used by the CLI to switch between filesystem and Eagle-catalog strategies.
- `MediaOrganizer`
  Organizes accepted media items into the destination tree, handling duplicates, conflicts, and sidecars.
- `OrganizerOptions`, `OrganizerResult`
  Configuration and result models for organization workflows.

## Best Practices

- **Run `organizer` with `--dry` first.** The command shows previews and logical outcomes before making changes.
- **Expect an interactive prompt** in `organizer`. The current implementation waits for `Enter` before proceeding.
- **Do not assume `organizer` moves files.** The CLI currently builds `OrganizerOptions(copy=True, ...)`, so it copies by default.
- **Treat `--eagletag` as an OR filter** when reading Eagle catalogs: any matching tag is enough to accept an item.
- **Remember that `--exclude` matches filenames, not full paths.**
- **Keep Eagle running** when using `EagleAPI` or `AsyncEagleAPI`.
- **Be careful with `sidegen`** in non-dry mode: existing `.xmp` files are deleted and recreated.
- **Install `exiftool`** if your workflow depends heavily on XMP generation and date extraction through `pylizlib` metadata helpers.

## Running Tests

### Install development dependencies

```bash
uv sync --group dev
```

### Run the full test suite

```bash
uv run pytest
```

### Run the Makefile targets

```bash
make test
make qa
```

### Important note about integration tests

The repository contains both pure/local tests and live integration tests.

From `test/conftest.py`, the full suite expects:

- Eagle.cool to be reachable through the local API,
- the repository's `TestCatalog.library` fixture to exist,
- integration scenarios that create/read real items in the catalog.

Examples of local tests that were validated successfully while preparing this README:

```bash
uv run pytest test/test_cli.py test/test_media_org.py test/test_async_api_extended.py test/test_organizer.py -q
```

## Contributing

There is currently **no dedicated `CONTRIBUTING.md`** in the repository, but the project already exposes a solid development workflow through `pyproject.toml` and `makefile`.

Suggested contribution flow:

1. Fork the repository.
2. Create a feature branch.
3. Install dependencies:

   ```bash
   uv sync --group dev
   ```

4. Run quality checks before opening a PR:

   ```bash
   make qa
   ```

5. Add or update tests when changing behavior.
6. Keep README/API examples aligned with real behavior.

The current toolchain includes:

- `pytest`
- `ruff`
- `mypy`
- `pdoc`
- `pyinstaller`

## Roadmap

> TODO: no explicit public roadmap file was found in the repository.

Based on the current codebase and changelog, likely future documentation candidates include:

- broader Eagle API coverage,
- more end-to-end workflow examples,
- clearer non-interactive/batch usage guidance for the CLI.

## FAQ

### Do I need Eagle.cool running to use `eagleliz`?

For the HTTP API clients (`EagleAPI`, `AsyncEagleAPI`), yes. They talk to Eagle's local API, which defaults to `http://localhost:41595/api`.

For local catalog parsing (`EagleLocalReader`, `organizer --eaglecatalog`, `sidegen`), some workflows can read directly from the `.library` contents on disk.

### Does `organizer` move or copy files?

The current CLI behavior copies files. The underlying engine supports both strategies, but the CLI currently constructs `OrganizerOptions` with `copy=True`.

### Is `organizer` safe for automation?

Partially. It supports dry-run mode and environment variables, but the command is still interactive because it waits for `Enter` before the final organization step.

### What output structure does `organizer` create?

With the current CLI defaults, files are organized under:

```text
<output>/<year>/<month>/
```

### Can I preserve Eagle tags and annotations in sidecars?

Yes. The XMP-related workflow attaches Eagle metadata to generated sidecars when that metadata is available on the media item.

## Support and Contact

The repository explicitly declares this maintainer information in `pyproject.toml`:

- **Author:** Gabliz
- **Email:** `gabliz.dev@gmail.com`

> TODO: add the canonical GitHub Issues / Discussions links if you want this section to point to public support channels.

## License

> TODO: no `LICENSE` file was found in the repository at the time this README was generated.

If you plan to publish or maintain this package as an open-source project, adding a license file should be a high-priority next step.

## Credits

- [Eagle.cool](https://eagle.cool) and its local API design.
- [`pylizlib`](https://pypi.org/project/pylizlib/) for shared media, metadata, and application helpers used throughout the project.
- [`Typer`](https://typer.tiangolo.com/) for the CLI.
- [`Rich`](https://rich.readthedocs.io/) for terminal rendering.
- [`tqdm`](https://tqdm.github.io/) for progress bars.
- [`httpx`](https://www.python-httpx.org/) and [`requests`](https://requests.readthedocs.io/) for HTTP integrations.

