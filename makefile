# ==============================================================================
#
#  _______     _________ _    _  ____  _   _
# |  __ \ \   / /__   __| |  | |/ __ \| \ | |
# | |__) \ \_/ /   | |  | |__| | |  | |  \| |
# |  ___/ \   /    | |  |  __  | |  | | . ` |
# | |      | |     | |  | |  | | |__| | |\  |
# |_|      |_|     |_|  |_|  |_|\____/|_| \_|
#
#  _____  _____   ____       _ ______ _____ _______
# |  __ \|  __ \ / __ \     | |  ____/ ____|__   __|
# | |__) | |__) | |  | |    | | |__ | |       | |
# |  ___/|  _  /| |  | |_   | |  __|| |       | |
# | |    | | \ \| |__| | |__| | |___| |____   | |
# |_|    |_|  \_\\____/ \____/|______\_____|  |_|
#
#  __  __          _  ________ ______ _____ _      ______
# |  \/  |   /\   | |/ /  ____|  ____|_   _| |    |  ____|
# | \  / |  /  \  | ' /| |__  | |__    | | | |    | |__
# | |\/| | / /\ \ |  < |  __| |  __|   | | | |    |  __|
# | |  | |/ ____ \| . \| |____| |     _| |_| |____| |____
# |_|  |_/_/    \_\_|\_\______|_|    |_____|______|______|
#
#                           VERSION 2.0.0
#
#  A reusable, self-documenting Makefile template for Python projects
#  managed with `uv`.
#
#  ► All project-specific variables live in project.mk  – edit THAT file.
#  ► Run `make` (no arguments) to see the list of available targets.
#
#  Sections
#  ─────────────────────────────────────────────────────────────────────────────
#    1. Platform Detection  – OS detection for cross-platform support
#    2. Help                – self-documenting target list
#    3. Environment         – install / setup via uv
#    4. Generate            – code generation from metadata
#    5. Quality             – lint · format · type-check · test
#    6. Build               – sdist · wheel · standalone executables
#    7. Docs                – API documentation with pdoc
#    8. Clean               – remove build artefacts and caches
#    9. Versioning          – bump version · create git tags
#   10. CI Helpers          – lightweight targets for GitHub Actions
#
# ==============================================================================

include project.mk


# ==============================================================================
#  1. PLATFORM DETECTION
#
#  Automatically detects the host OS so that platform-specific tools
#  (e.g. icon formats for PyInstaller, sed flavour for in-place edits)
#  can be selected without any manual configuration.
# ==============================================================================

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
    OS_NAME     := macos
    SED_INPLACE := sed -i ''
else ifeq ($(UNAME_S),Linux)
    OS_NAME     := linux
    SED_INPLACE := sed -i
else
    OS_NAME     := windows
    SED_INPLACE := sed -i
endif


# ==============================================================================
#  2. HELP
#
#  The default target. Scans all included Makefiles for lines of the form
#      ## target-name  – Short description
#  and prints a formatted, colour-coded reference table.
# ==============================================================================

.DEFAULT_GOAL := help

## help              – Show this help message and exit
.PHONY: help
help:
	@printf "\n"
	@printf "  \033[1mPython Project Makefile\033[0m\n"
	@printf "  ──────────────────────────────────────────────────────\n"
	@grep -E '^## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS="## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$2, $$3}' 2>/dev/null \
		|| grep -E '^## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS="## "}; {printf "  %-26s\n", $$2}'
	@printf "\n"


# ==============================================================================
#  3. ENVIRONMENT
#
#  ______ _   ___      _______ _____   ____  _   _ __  __ ______ _   _ _______
# |  ____| \ | \ \    / /_   _|  __ \ / __ \| \ | |  \/  |  ____| \ | |__   __|
# | |__  |  \| |\ \  / /  | | | |__) | |  | |  \| | \  / | |__  |  \| |  | |
# |  __| | . ` | \ \/ /   | | |  _  /| |  | | . ` | |\/| |  __| | . ` |  | |
# | |____| |\  |  \  /   _| |_| | \ \| |__| | |\  | |  | | |____| |\  |  | |
# |______|_| \_|   \/   |_____|_|  \_\\____/|_| \_|_|  |_|______|_| \_|  |_|
#
#  Setup and install targets for the local development environment.
#  Requires `uv` to be installed: https://docs.astral.sh/uv/
# ==============================================================================

## install              – Sync all dependency groups and extras via uv
.PHONY: install
install:
	uv sync
	uv sync --all-extras

## install-all          – Install configured Python, sync all groups, and run uv build
.PHONY: install-all
install-all:
	uv python install $(CI_PYTHON_VERSION)
	uv sync --all-groups
	uv build

## install-dev          – Sync only the dev dependency group
.PHONY: install-dev
install-dev:
	uv sync --group dev

## install-pyinstaller  – Add PyInstaller to the dev group (needed for build-exe targets)
.PHONY: install-pyinstaller
install-pyinstaller:
	uv add --group dev pyinstaller

## install-inno         – Install Inno Setup via Chocolatey (Windows only)
.PHONY: install-inno
install-inno:
	@if [ "$(OS_NAME)" != "windows" ]; then \
		echo "Error: install-inno is available only on Windows."; \
		exit 1; \
	fi
	choco install innosetup


# ==============================================================================
#  4. GENERATE
#
#    _____ ______ _   _ ______ _____         _______ ______
#   / ____|  ____| \ | |  ____|  __ \     /\|__   __|  ____|
#  | |  __| |__  |  \| | |__  | |__) |   /  \  | |  | |__
#  | | |_ |  __| | . ` |  __| |  _  /   / /\ \ | |  |  __|
#  | |__| | |____| |\  | |____| | \ \  / ____ \| |  | |____
#   \_____|______|_| \_|______|_|  \_\/_/    \_\_|  |______|
#
#  Targets that auto-generate source files from project metadata.
#  Qt resource generation lives in qt.mk (include it from project.mk if needed).
# ==============================================================================

## gen-project-py       – Generate $(FILE_PROJECT_PY_GENERATED) from pyproject.toml
#
#  Reads the [project] table from pyproject.toml and writes a plain Python
#  module (zero external dependencies) that exposes name, version, description,
#  requires_python, and authors as module-level constants.
.PHONY: gen-project-py
gen-project-py:
	@printf '%s\n' \
		'from pathlib import Path' \
		'import sys' \
		'import tomllib' \
		'pyproject_path = Path("$(FILE_PROJECT_TOML)")' \
		'py_file = Path("$(FILE_PROJECT_PY_GENERATED)")' \
		'try:' \
		'    if not pyproject_path.exists():' \
		'        raise FileNotFoundError(f"File {pyproject_path} does not exist.")' \
		'    with pyproject_path.open("rb") as f:' \
		'        data = tomllib.load(f)' \
		'    project = data.get("project", {})' \
		'    raw_authors = project.get("authors", [])' \
		'    authors = []' \
		'    for entry in raw_authors:' \
		'        name = entry.get("name")' \
		'        email = entry.get("email")' \
		'        if name or email:' \
		'            authors.append((name, email))' \
		'    info = {' \
		'        "name": project.get("name"),' \
		'        "version": project.get("version"),' \
		'        "description": project.get("description"),' \
		'        "requires_python": project.get("requires-python"),' \
		'        "authors": authors,' \
		'    }' \
		'    authors_repr = "[" + ", ".join(' \
		'        f"({repr(name)}, {repr(email)})"' \
		'        for name, email in info["authors"]' \
		'    ) + "]"' \
		'    lines = [' \
		'        "# fmt: off",' \
		'        "name = " + repr(info["name"]),' \
		'        "version = " + repr(info["version"]),' \
		'        "description = " + repr(info["description"]),' \
		'        "requires_python = " + repr(info["requires_python"]),' \
		'        "authors = " + authors_repr,' \
		'        "# fmt: on",' \
		'    ]' \
		'    py_file.parent.mkdir(parents=True, exist_ok=True)' \
		'    with py_file.open("w", encoding="utf-8") as f:' \
		'        f.write("\n".join(lines) + "\n")' \
		'    print(f"Generated: {py_file}")' \
		'except Exception as e:' \
		'    print(f"Error: {e}", file=sys.stderr)' \
		'    raise SystemExit(1)' | uv run python -

## gen-inno-iss         – Generate $(INNO_SETUP_FILE) from project.mk installer variables
#
#  Creates a clean, template-friendly Inno Setup script that packages the
#  executable configured in project.mk. The script version is resolved from
#  `uv version --short`, so release bumps are reflected automatically.
.PHONY: gen-inno-iss
gen-inno-iss:
	@printf '%s\n' \
		'from pathlib import Path' \
		'import sys' \
		'' \
		'def esc(value: str) -> str:' \
		'    return value.replace("\"", "\"\"")' \
		'' \
		'args = sys.argv[1:]' \
		'target = Path(args[0])' \
		'version_define = args[1]' \
		'app_name = args[2]' \
		'app_publisher = args[3]' \
		'app_icon = args[4]' \
		'app_exe = args[5]' \
		'default_dir_name = args[6]' \
		'default_group_name = args[7]' \
		'output_dir = args[8]' \
		'output_base_filename = args[9]' \
		'compression = args[10]' \
		'solid_compression = args[11]' \
		'app_version = args[12]' \
		'values = {' \
		'    "MyAppName": esc(app_name),' \
		'    version_define: esc(app_version),' \
		'    "MyAppPublisher": esc(app_publisher),' \
		'    "MyAppExe": esc(app_exe.replace("/", "\\\\")),' \
		'    "MyAppExeName": esc(Path(app_exe).name),' \
		'    "MyAppIcon": esc(app_icon.replace("/", "\\\\")),' \
		'    "MyAppDefaultDirName": esc(default_dir_name),' \
		'    "MyAppDefaultGroupName": esc(default_group_name),' \
		'    "MyAppOutputDir": esc(output_dir.replace("/", "\\\\")),' \
		'    "MyAppOutputBaseFilename": esc(output_base_filename),' \
		'    "MyAppCompression": esc(compression),' \
		'    "MyAppSolidCompression": esc(solid_compression),' \
		'}' \
		'defines = [f"#define {key} \"{value}\"" for key, value in values.items()]' \
		'content = "\n".join([' \
		'    "; -----------------------------------------------------------------------------",' \
		'    "; Auto-generated by: make gen-inno-iss",' \
		'    "; Edit installer settings in project.mk, then regenerate this file.",' \
		'    "; -----------------------------------------------------------------------------",' \
		'    "", *defines, "",' \
		'    "[Setup]", "AppName={#MyAppName}", f"AppVersion={{#{version_define}}}",' \
		'    "AppPublisher={#MyAppPublisher}", "DefaultDirName={#MyAppDefaultDirName}",' \
		'    "DefaultGroupName={#MyAppDefaultGroupName}", "OutputDir={#MyAppOutputDir}",' \
		'    "OutputBaseFilename={#MyAppOutputBaseFilename}", "Compression={#MyAppCompression}",' \
		'    "SolidCompression={#MyAppSolidCompression}", "SetupIconFile={#MyAppIcon}",' \
		'    "ArchitecturesInstallIn64BitMode=x64compatible", "WizardStyle=modern", "",' \
		'    "[Languages]", "Name: \"english\"; MessagesFile: \"compiler:Default.isl\"", "",' \
		'    "[Tasks]", "Name: \"desktopicon\"; Description: \"{cm:CreateDesktopIcon}\"; GroupDescription: \"{cm:AdditionalIcons}\"; Flags: unchecked", "",' \
		'    "[Files]", "Source: \"{#MyAppExe}\"; DestDir: \"{app}\"; Flags: ignoreversion", "",' \
		'    "[Icons]", "Name: \"{group}\\{#MyAppName}\"; Filename: \"{app}\\{#MyAppExeName}\"",' \
		'    "Name: \"{autodesktop}\\{#MyAppName}\"; Filename: \"{app}\\{#MyAppExeName}\"; Tasks: desktopicon", "",' \
		'    "[Run]", "Filename: \"{app}\\{#MyAppExeName}\"; Description: \"Launch {#MyAppName}\"; Flags: nowait postinstall skipifsilent", "",' \
		'])' \
		'target.parent.mkdir(parents=True, exist_ok=True)' \
		'target.write_text(content, encoding="utf-8")' \
		'print(f"Generated: {target}")' \
	| uv run python - \
		"$(INNO_SETUP_FILE)" \
		"$(INNO_SETUP_VERSION_VARIABLE)" \
		"$(INNO_APP_NAME)" \
		"$(INNO_APP_PUBLISHER)" \
		"$(INNO_APP_ICON)" \
		"$(INNO_APP_EXE)" \
		"$(INNO_DEFAULT_DIR_NAME)" \
		"$(INNO_DEFAULT_GROUP_NAME)" \
		"$(INNO_OUTPUT_DIR)" \
		"$(INNO_OUTPUT_BASE_FILENAME)" \
		"$(INNO_COMPRESSION)" \
		"$(INNO_SOLID_COMPRESSION)" \
		"$$(uv version --short)"


# ==============================================================================
#  5. QUALITY
#
#    ____  _    _         _      _____ _________     __
#   / __ \| |  | |  /\   | |    |_   _|__   __\ \   / /
#  | |  | | |  | | /  \  | |      | |    | |   \ \_/ /
#  | |  | | |  | |/ /\ \ | |      | |    | |    \   /
#  | |__| | |__| / ____ \| |____ _| |_   | |     | |
#   \___\_\\____/_/    \_\______|_____|  |_|     |_|
#
#  Lint, format, type-check, and test the source code.
#  All tools are run through uv so no global installs are required.
# ==============================================================================

## lint                 – Run Ruff linter (check only, no changes written)
.PHONY: lint
lint:
	uv run ruff check .

## lint-fix             – Run Ruff linter and auto-fix safe issues
.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix .

## format               – Format all Python files with Ruff formatter
.PHONY: format
format:
	uv run ruff format .

## format-check         – Check formatting without making changes (CI-safe)
.PHONY: format-check
format-check:
	uv run ruff format --check .

## type-check           – Run static type analysis with mypy
.PHONY: type-check
type-check:
	uv run mypy $(PYTHON_MAIN_PACKAGE)

## test                 – Run the full test suite with pytest
.PHONY: test
test:
	uv run pytest

## test-cov             – Run tests with a terminal coverage report
.PHONY: test-cov
test-cov:
	uv run pytest --cov=$(PYTHON_MAIN_PACKAGE) --cov-report=term-missing

## qa                   – Run all quality gates: lint · format-check · type-check · test
.PHONY: qa
qa: lint format-check type-check test


# ==============================================================================
#  6. BUILD
#
#   ____  _    _ _____ _      _____
#  |  _ \| |  | |_   _| |    |  __ \
#  | |_) | |  | | | | | |    | |  | |
#  |  _ <| |  | | | | | |    | |  | |
#  | |_) | |__| |_| |_| |____| |__| |
#  |____/ \____/|_____|______|_____/
#
#  Build distribution packages (wheel + sdist) and standalone executables.
#  PyInstaller targets require `install-pyinstaller` to have been run first.
# ==============================================================================

## build                – Full build: clean → gen-project-py → uv build
.PHONY: build
build: clean gen-project-py build-uv

## build-uv             – Build sdist and wheel with uv (no clean or generate step)
.PHONY: build-uv
build-uv:
	uv build

## build-exe            – Build one-folder executables with PyInstaller for each app in APPS_LIST
#
#  Iterates over APPS_LIST. For each entry <id> the following companion
#  variables must be defined in project.mk:
#    <id>_NAME   output binary name (without extension)
#    <id>_MAIN   entry-point script passed to PyInstaller
#    <id>_ICO    Windows icon  (.ico)
#    <id>_ICNS   macOS icon    (.icns)
.PHONY: build-exe
build-exe:
	$(foreach app,$(APPS_LIST),\
		uv run pyinstaller --noconfirm --windowed \
			--icon=$(if $(filter Darwin,$(UNAME_S)),$($(app)_ICNS),$($(app)_ICO)) \
			--name=$($(app)_NAME)-$(OS_NAME) \
			$($(app)_MAIN); \
	)

## build-exe-onefile    – Build single-file executables with PyInstaller for each app in APPS_LIST
.PHONY: build-exe-onefile
build-exe-onefile:
	$(foreach app,$(APPS_LIST),\
		uv run pyinstaller --noconfirm --windowed --onefile \
			--icon=$(if $(filter Darwin,$(UNAME_S)),$($(app)_ICNS),$($(app)_ICO)) \
			--name=$($(app)_NAME)-$(OS_NAME) \
			$($(app)_MAIN); \
	)

## build-app            – Full app build: clean → gen-project-py → uv build → build-exe
.PHONY: build-app
build-app: clean gen-project-py build-uv build-exe

## build-app-onefile    – Full app build using the --onefile PyInstaller mode
.PHONY: build-app-onefile
build-app-onefile: clean gen-project-py build-uv build-exe-onefile

## installer            – Run Inno Setup to produce the Windows installer (Windows only)
.PHONY: installer
installer: gen-inno-iss
ifeq ($(filter Darwin Linux,$(UNAME_S)),)
	ISCC.exe $(INNO_SETUP_FILE)
else
	@echo "Error: The installer target can only be run on Windows."
	@exit 1
endif

## build-installer      – Full pipeline including the Windows installer step
.PHONY: build-installer
build-installer: build-app-onefile installer


# ==============================================================================
#  7. DOCS
#
#   _____   ____   _____  _____
#  |  __ \ / __ \ / ____|/ ____|
#  | |  | | |  | | |    | (___
#  | |  | | |  | | |     \___ \
#  | |__| | |__| | |____ ____) |
#  |_____/ \____/ \_____|_____/
#
#  Generate API documentation with pdoc.
#  Install pdoc first: `uv add --group dev pdoc`
# ==============================================================================

## docs                 – Generate HTML docs in docs/ using pdoc (markdown format)
.PHONY: docs
docs:
	uv run pdoc -o docs -d markdown $(PYTHON_MAIN_PACKAGE)

## docs-open            – Generate docs and open index.html in the default browser
.PHONY: docs-open
docs-open: docs
ifeq ($(UNAME_S),Darwin)
	open docs/index.html
else
	xdg-open docs/index.html
endif


# ==============================================================================
#  8. CLEAN
#
#    _____ _      ______          _   _
#   / ____| |    |  ____|   /\   | \ | |
#  | |    | |    | |__     /  \  |  \| |
#  | |    | |    |  __|   / /\ \ | . ` |
#  | |____| |____| |____ / ____ \| |\  |
#   \_____|______|______/_/    \_\_| \_|
#
#  Remove generated files, build artefacts, and caches.
# ==============================================================================

## clean                – Remove build artefacts and generated files (safe pre-build step)
.PHONY: clean
clean: clean-build clean-cache clean-generated

## clean-all            – Remove everything including generated docs
.PHONY: clean-all
clean-all: clean clean-docs

## clean-build          – Remove dist/, build/, .egg-info, and PyInstaller .spec files
.PHONY: clean-build
clean-build:
	- rm -rf dist
	- rm -rf build
	- rm -rf $(PYTHON_MAIN_PACKAGE).egg-info
	- rm -f *.spec

## clean-cache          – Remove Python bytecode, pytest, mypy, and ruff caches
.PHONY: clean-cache
clean-cache:
	- rm -rf __pycache__
	- rm -rf .pytest_cache
	- rm -rf .mypy_cache
	- rm -rf .ruff_cache
	- find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

## clean-docs           – Remove the generated docs/ directory
.PHONY: clean-docs
clean-docs:
	- rm -rf docs

## clean-generated      – Remove only the auto-generated Python source files
.PHONY: clean-generated
clean-generated:
	@echo "Cleaning generated files..."
	- rm -f $(FILE_PROJECT_PY_GENERATED)


# ==============================================================================
#  9. VERSIONING
#
# __      ________ _____   _____ _____ ____  _   _ _____ _   _  _____
# \ \    / /  ____|  __ \ / ____|_   _/ __ \| \ | |_   _| \ | |/ ____|
#  \ \  / /| |__  | |__) | (___   | || |  | |  \| | | | |  \| | |  __
#   \ \/ / |  __| |  _  / \___ \  | || |  | | . ` | | | | . ` | | |_ |
#    \  /  | |____| | \ \ ____) |_| || |__| | |\  |_| |_| |\  | |__| |
#     \/   |______|_|  \_\_____/|_____\____/|_| \_|_____|_| \_|\_____|
#
#  Bump the project version (managed by uv) and manage git release tags.
#
#  Typical workflows
#  ─────────────────────────────────────────────────────────────────────────────
#    Patch release  →  make release-patch-tag
#    Minor release  →  make release-minor-tag
#    Pre-release    →  make release-patch-beta-tag
# ==============================================================================

## bump-patch-beta      – Bump to next patch pre-release, e.g. 1.2.3 → 1.2.4b1
.PHONY: bump-patch-beta
bump-patch-beta:
	uv version --bump patch --bump beta

## bump-patch           – Bump the patch component, e.g. 1.2.3 → 1.2.4
.PHONY: bump-patch
bump-patch:
	uv version --bump patch

## bump-minor           – Bump the minor component, e.g. 1.2.3 → 1.3.0
.PHONY: bump-minor
bump-minor:
	uv version --bump minor

## bump-major           – Bump the major component, e.g. 1.2.3 → 2.0.0
.PHONY: bump-major
bump-major:
	uv version --bump major

# ── Internal helper ──────────────────────────────────────────────────────────
#
#  Shared recipe executed after every version bump target.
#  Steps:
#    1. Optionally patches the version string inside the Inno Setup .iss file.
#    2. Commits all staged changes with a "bump: vX.Y.Z" message.
#    3. Pull-rebases to incorporate remote changes, then pushes.
define _release_impl
	@VERSION=$$(uv version --short); \
	echo "Releasing version $$VERSION …"; \
	if [ -f "$(INNO_SETUP_FILE)" ]; then \
		echo "  Updating Inno Setup version …"; \
		$(SED_INPLACE) \
			"s/#define $(INNO_SETUP_VERSION_VARIABLE) \"[^\"]*\"/#define $(INNO_SETUP_VERSION_VARIABLE) \"$$VERSION\"/" \
			$(INNO_SETUP_FILE); \
	fi; \
	git commit -am "bump: v$$VERSION"; \
	git pull --rebase; \
	git push
endef

## release-patch-beta   – bump-patch-beta + gen-project-py + commit & push
.PHONY: release-patch-beta
release-patch-beta: bump-patch-beta gen-project-py
	$(call _release_impl)

## release-patch        – bump-patch + gen-project-py + commit & push
.PHONY: release-patch
release-patch: bump-patch gen-project-py
	$(call _release_impl)

## release-minor        – bump-minor + gen-project-py + commit & push
.PHONY: release-minor
release-minor: bump-minor gen-project-py
	$(call _release_impl)

## release-major        – bump-major + gen-project-py + commit & push
.PHONY: release-major
release-major: bump-major gen-project-py
	$(call _release_impl)

## tag                  – Pull latest, create a v-prefixed git tag from uv version, and push
.PHONY: tag
tag:
	git pull
	git tag v$$(uv version --short)
	git push origin v$$(uv version --short)

## release-patch-beta-tag – release-patch-beta + tag
.PHONY: release-patch-beta-tag
release-patch-beta-tag: release-patch-beta tag

## release-patch-tag    – release-patch + tag
.PHONY: release-patch-tag
release-patch-tag: release-patch tag

## release-minor-tag    – release-minor + tag
.PHONY: release-minor-tag
release-minor-tag: release-minor tag

## release-major-tag    – release-major + tag
.PHONY: release-major-tag
release-major-tag: release-major tag


# ==============================================================================
# 10. CI HELPERS
#
#    _____ _____   _    _ ______ _      _____  ______ _____   _____
#   / ____|_   _| | |  | |  ____| |    |  __ \|  ____|  __ \ / ____|
#  | |      | |   | |__| | |__  | |    | |__) | |__  | |__) | (___
#  | |      | |   |  __  |  __| | |    |  ___/|  __| |  _  / \___ \
#  | |____ _| |_  | |  | | |____| |____| |    | |____| | \ \ ____) |
#   \_____|_____| |_|  |_|______|______|_|    |______|_|  \_\_____/
#
#  Make-first targets consumed by GitHub Actions workflows.
#  Keep all shell logic here so workflow files stay short and generic.
# ==============================================================================

## ci-setup               – Prepare CI environment (install Python via uv + sync all groups)
.PHONY: ci-setup
ci-setup:
	uv python install $(CI_PYTHON_VERSION)
	uv sync --all-groups

## ci-quality             – Run CI quality gates; skip tests when CI_RUN_TESTS=0
.PHONY: ci-quality
ci-quality:
	@if [ "$(CI_RUN_TESTS)" = "1" ]; then \
		echo "CI_RUN_TESTS=1 -> running full qa (including tests)"; \
		$(MAKE) --no-print-directory qa; \
	else \
		echo "CI_RUN_TESTS=0 -> running lint, format-check, and type-check only"; \
		$(MAKE) --no-print-directory lint format-check type-check; \
	fi

## ci-export-config       – Export CI configuration values to $GITHUB_OUTPUT
.PHONY: ci-export-config
ci-export-config:
	@if [ -z "$$GITHUB_OUTPUT" ]; then \
		echo "Error: GITHUB_OUTPUT is not set."; \
		exit 1; \
	fi
	@echo "release_branch=$(RELEASE_CHANGELOG_TARGET_BRANCH)" >> "$$GITHUB_OUTPUT"
	@echo "windows_installer_enabled=$(ENABLE_WINDOWS_INSTALLER)" >> "$$GITHUB_OUTPUT"
	@echo "build_linux=$(CI_BUILD_LINUX)" >> "$$GITHUB_OUTPUT"
	@echo "build_macos=$(CI_BUILD_MACOS)" >> "$$GITHUB_OUTPUT"
	@echo "build_windows=$(CI_BUILD_WINDOWS)" >> "$$GITHUB_OUTPUT"
	@echo "enable_pypi_publish=$(CI_ENABLE_PYPI_PUBLISH)" >> "$$GITHUB_OUTPUT"
	@echo "pypi_environment=$(CI_PYPI_ENVIRONMENT)" >> "$$GITHUB_OUTPUT"
	@echo "enable_dockerhub_publish=$(CI_ENABLE_DOCKERHUB_PUBLISH)" >> "$$GITHUB_OUTPUT"
	@echo "dockerhub_environment=$(CI_DOCKERHUB_ENVIRONMENT)" >> "$$GITHUB_OUTPUT"
	@echo "dockerhub_image=$(CI_DOCKERHUB_IMAGE)" >> "$$GITHUB_OUTPUT"
	@echo "dockerfile=$(CI_DOCKERFILE)" >> "$$GITHUB_OUTPUT"
	@echo "docker_build_context=$(CI_DOCKER_BUILD_CONTEXT)" >> "$$GITHUB_OUTPUT"
	@echo "docker_push_latest=$(CI_DOCKER_PUSH_LATEST)" >> "$$GITHUB_OUTPUT"
	@echo "changelog_file=$(CI_CHANGELOG_FILE)" >> "$$GITHUB_OUTPUT"
	@echo "release_notes_file=$(CI_RELEASE_NOTES_FILE)" >> "$$GITHUB_OUTPUT"
	@echo "git_cliff_config=$(CI_GIT_CLIFF_CONFIG)" >> "$$GITHUB_OUTPUT"
	@{ \
		echo "release_artifacts<<EOF"; \
		$(MAKE) --no-print-directory ci-release-artifacts; \
		echo "EOF"; \
	} >> "$$GITHUB_OUTPUT"

## ci-install-git-cliff   – Ensure git-cliff is available in CI
.PHONY: ci-install-git-cliff
ci-install-git-cliff:
	uv tool install git-cliff

## ci-generate-changelog  – Generate the full changelog file configured in CI_CHANGELOG_FILE
.PHONY: ci-generate-changelog
ci-generate-changelog:
	uvx git-cliff --config $(CI_GIT_CLIFF_CONFIG) --output $(CI_CHANGELOG_FILE)

## ci-generate-release-notes – Generate latest release notes into CI_RELEASE_NOTES_FILE
.PHONY: ci-generate-release-notes
ci-generate-release-notes:
	uvx git-cliff --config $(CI_GIT_CLIFF_CONFIG) --latest --strip header > $(CI_RELEASE_NOTES_FILE)

## ci-commit-changelog    – Commit and push changelog updates to RELEASE_CHANGELOG_TARGET_BRANCH
.PHONY: ci-commit-changelog
ci-commit-changelog:
	git config user.name "github-actions[bot]"
	git config user.email "github-actions[bot]@users.noreply.github.com"
	git add $(CI_CHANGELOG_FILE)
	@if git diff --staged --quiet; then \
		echo "No changes to $(CI_CHANGELOG_FILE)"; \
	else \
		git commit -m "chore: update changelog [skip ci]"; \
		git fetch origin; \
		git push origin "HEAD:$(RELEASE_CHANGELOG_TARGET_BRANCH)" || echo "Push failed, continuing..."; \
	fi

## ci-build-release-assets – Build release assets for the current runner OS
.PHONY: ci-build-release-assets
ci-build-release-assets:
	@if [ "$(OS_NAME)" = "windows" ] && [ "$(ENABLE_WINDOWS_INSTALLER)" = "1" ]; then \
		$(MAKE) --no-print-directory install-inno; \
		$(MAKE) --no-print-directory build-installer; \
	else \
		$(MAKE) --no-print-directory build-exe-onefile; \
	fi

## ci-publish-pypi        – Publish package artifacts to PyPI (requires UV_PUBLISH_TOKEN)
.PHONY: ci-publish-pypi
ci-publish-pypi:
	uv publish

## ci-export-docker-tag   – Export Docker tag (release tag or pyproject version) to $GITHUB_OUTPUT
.PHONY: ci-export-docker-tag
ci-export-docker-tag:
	@if [ -z "$$GITHUB_OUTPUT" ]; then \
		echo "Error: GITHUB_OUTPUT is not set."; \
		exit 1; \
	fi
	@TAG="$$GITHUB_REF_NAME"; \
	if [ "$$GITHUB_REF_TYPE" != "tag" ] || [ -z "$$TAG" ]; then \
		TAG=$$(python3 -c 'from pathlib import Path; import tomllib; data=tomllib.loads(Path("$(FILE_PROJECT_TOML)").read_text(encoding="utf-8")); print(data.get("project", {}).get("version", "latest"))'); \
	fi; \
	echo "docker_image_tag=$$TAG" >> "$$GITHUB_OUTPUT"; \
	echo "Resolved Docker image tag: $$TAG"

## ci-docker-login        – Login to Docker Hub using DOCKERHUB_USERNAME and DOCKERHUB_TOKEN
.PHONY: ci-docker-login
ci-docker-login:
	@if [ -z "$$DOCKERHUB_USERNAME" ] || [ -z "$$DOCKERHUB_TOKEN" ]; then \
		echo "Error: DOCKERHUB_USERNAME and DOCKERHUB_TOKEN must be set."; \
		exit 1; \
	fi
	@echo "$$DOCKERHUB_TOKEN" | docker login --username "$$DOCKERHUB_USERNAME" --password-stdin

## ci-docker-build        – Build Docker image for DOCKER_IMAGE_TAG using project.mk Docker settings
.PHONY: ci-docker-build
ci-docker-build:
	@if [ -z "$$DOCKER_IMAGE_TAG" ]; then \
		echo "Error: DOCKER_IMAGE_TAG is not set."; \
		exit 1; \
	fi
	@if [ ! -f "$(CI_DOCKERFILE)" ]; then \
		echo "Error: Dockerfile not found at $(CI_DOCKERFILE)."; \
		exit 1; \
	fi
	docker build \
		-f "$(CI_DOCKERFILE)" \
		-t "$(CI_DOCKERHUB_IMAGE):$$DOCKER_IMAGE_TAG" \
		"$(CI_DOCKER_BUILD_CONTEXT)"

## ci-publish-dockerhub   – Build and push Docker image (and optional latest tag) to Docker Hub
.PHONY: ci-publish-dockerhub
ci-publish-dockerhub: ci-docker-build
	@docker push "$(CI_DOCKERHUB_IMAGE):$$DOCKER_IMAGE_TAG"
	@if [ "$(CI_DOCKER_PUSH_LATEST)" = "1" ]; then \
		docker tag "$(CI_DOCKERHUB_IMAGE):$$DOCKER_IMAGE_TAG" "$(CI_DOCKERHUB_IMAGE):latest"; \
		docker push "$(CI_DOCKERHUB_IMAGE):latest"; \
	fi

## ci-release-branch      – Print RELEASE_CHANGELOG_TARGET_BRANCH
.PHONY: ci-release-branch
ci-release-branch:
	@echo $(RELEASE_CHANGELOG_TARGET_BRANCH)

## ci-windows-installer   – Print ENABLE_WINDOWS_INSTALLER (1 or 0)
.PHONY: ci-windows-installer
ci-windows-installer:
	@echo $(ENABLE_WINDOWS_INSTALLER)

## ci-release-artifacts   – Print each RELEASE_ARTIFACTS glob pattern on its own line
.PHONY: ci-release-artifacts
ci-release-artifacts:
	@set -f; for pattern in $(RELEASE_ARTIFACTS); do printf '%s\n' "$$pattern"; done

## ci-print-release-target-branch – Legacy alias of ci-release-branch
.PHONY: ci-print-release-target-branch
ci-print-release-target-branch: ci-release-branch

## ci-print-windows-installer-enabled – Legacy alias of ci-windows-installer
.PHONY: ci-print-windows-installer-enabled
ci-print-windows-installer-enabled: ci-windows-installer

## ci-print-release-artifacts – Legacy alias of ci-release-artifacts
.PHONY: ci-print-release-artifacts
ci-print-release-artifacts: ci-release-artifacts

