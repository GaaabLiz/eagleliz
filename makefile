#    $$\      $$\  $$$$$$\  $$\   $$\ $$$$$$$$\ $$$$$$$$\ $$$$$$\ $$\       $$$$$$$$\
#    $$$\    $$$ |$$  __$$\ $$ | $$  |$$  _____|$$  _____|\_$$  _|$$ |      $$  _____|
#    $$$$\  $$$$ |$$ /  $$ |$$ |$$  / $$ |      $$ |        $$ |  $$ |      $$ |
#    $$\$$\$$ $$ |$$$$$$$$ |$$$$$  /  $$$$$\    $$$$$\      $$ |  $$ |      $$$$$\
#    $$ \$$$  $$ |$$  __$$ |$$  $$<   $$  __|   $$  __|     $$ |  $$ |      $$  __|
#    $$ |\$  /$$ |$$ |  $$ |$$ |\$$\  $$ |      $$ |        $$ |  $$ |      $$ |
#    $$ | \_/ $$ |$$ |  $$ |$$ | \$$\ $$$$$$$$\ $$ |      $$$$$$\ $$$$$$$$\ $$$$$$$$\
#    \__|     \__|\__|  \__|\__|  \__|\________|\__|      \______|\________|\________|
#
#                               PYTHON PROJECT MAKEFILE
#
#                                   VERSION 1.1.2

include project.mk





#      ______ _   ___      _______ _____   ____  __  __ ______ _   _ _______
#     |  ____| \ | \ \    / /_   _|  __ \ / __ \|  \/  |  ____| \ | |__   __|
#     | |__  |  \| |\ \  / /  | | | |__) | |  | | \  / | |__  |  \| |  | |
#     |  __| | . ` | \ \/ /   | | |  _  /| |  | | |\/| |  __| | . ` |  | |
#     | |____| |\  |  \  /   _| |_| | \ \| |__| | |  | | |____| |\  |  | |
#     |______|_| \_|   \/   |_____|_|  \_\\____/|_|  |_|______|_| \_|  |_|


# == PLATFORM DETECTION ==
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    OS_NAME := macos
else ifeq ($(UNAME_S),Linux)
    OS_NAME := linux
else
    OS_NAME := windows
endif


# Rule to create a virtual environment and install dependencies
install-env:
	uv sync
	uv sync --all-extras

init-uv:
	uv python install 3.12
	uv sync --all-groups
	uv build

install-pyinstaller:
	uv add --group dev pyinstaller

install-inno-setup:
	choco install innosetup





#       _____ _      ______          _   _
#      / ____| |    |  ____|   /\   | \ | |
#     | |    | |    | |__     /  \  |  \| |
#     | |    | |    |  __|   / /\ \ | . ` |
#     | |____| |____| |____ / ____ \| |\  |
#      \_____|______|______/_/    \_\_| \_|

# Command to clean build artifacts
clean-build:
	- rm -rf dist
	- rm -rf build
	- rm -rf $(PYTHON_MAIN_PACKAGE).egg-info
	- rm -f *.spec

# Command to clean Python cache files
clean-cache:
	- rm -rf __pycache__
	- rm -rf .pytest_cache

# Command to clean generated documentation
clean-docs:
	- rm -rf docs

# Command to clean all generated files
clean-generated:
	@echo "CLeaning generated files..."
	- rm -f $(FILE_PROJECT_PY_GENERATED)
	- rm -f Output

# Aggregate clean command
clean: clean-build clean-cache clean-generated





#       _____ ______ _   _ ______ _____         _______ ______
#      / ____|  ____| \ | |  ____|  __ \     /\|__   __|  ____|
#     | |  __| |__  |  \| | |__  | |__) |   /  \  | |  | |__
#     | | |_ |  __| | . ` |  __| |  _  /   / /\ \ | |  |  __|
#     | |__| | |____| |\  | |____| | \ \  / ____ \| |  | |____
#      \_____|______|_| \_|______|_|  \_\/_/    \_\_|  |______|

gen-project-py:
	uv run pyliz gen-project-py $(FILE_PROJECT_TOML) $(FILE_PROJECT_PY_GENERATED)

gen-qt-res-py:
	$(QT_COMMAND_GEN_RES) $(QT_QRC_FILE) -o $(QT_RESOURCE_PY); \

installer:
ifeq ($(filter Darwin Linux,$(shell uname)),)
	ISCC.exe $(INNO_SETUP_FILE)
else
	@echo "Error: The installer can only be built on Windows."
	@exit 1
endif

build-uv:
	uv build

build-exe:
	$(foreach app,$(APPS_LIST),\
		uv run pyinstaller --windowed \
		--icon=$(if $(filter Darwin,$(shell uname)),$($(app)_ICNS),$($(app)_ICO)) \
		--name=$($(app)_NAME)-$(OS_NAME) \
		$($(app)_MAIN); \
	)

build-exe-onefile:
	$(foreach app,$(APPS_LIST),\
		uv run pyinstaller --windowed --onefile \
		--icon=$(if $(filter Darwin,$(shell uname)),$($(app)_ICNS),$($(app)_ICO)) \
		--name=$($(app)_NAME)-$(OS_NAME) \
		$($(app)_MAIN); \
	)

docs-gen:
	pdoc -o docs -d markdown $(PYTHON_MAIN_PACKAGE)

build-app: clean gen-project-py build-uv build-exe

build-app-onefile: clean gen-project-py build-uv build-exe-onefile

build-installer: build-app installer





#     __      _______  _____
#     \ \    / / ____|/ ____|
#      \ \  / / |    | (___
#       \ \/ /| |     \___ \
#        \  / | |____ ____) |
#         \/   \_____|_____/
#
#

uv-bump-patch-beta:
	uv version --bump patch --bump beta

uv-bump-patch:
	uv version --bump patch

uv-bump-minor:
	uv version --bump minor

uv-bump-major:
	uv version --bump major

define upgrade_version_impl
	@VERSION=$$(uv version --short); \
	if [ -f $(INNO_SETUP_FILE) ]; then \
		echo "Inno setup script found. upgrading version to $$VERSION..."; \
		sed -i "s/#define $(INNO_SETUP_VERSION_VARIABLE) \"[^\"]*\"/#define $(INNO_SETUP_VERSION_VARIABLE) \"$$VERSION\"/" $(INNO_SETUP_FILE); \
	fi; \
	git commit -am "bump: Bump version to $$VERSION"; \
	git push
endef

upgrade-patch-beta: uv-bump-patch-beta gen-project-py
	$(upgrade_version_impl)

upgrade-patch: uv-bump-patch gen-project-py
	$(upgrade_version_impl)

upgrade-minor: uv-bump-minor gen-project-py
	$(upgrade_version_impl)

upgrade-major: uv-bump-major gen-project-py
	$(upgrade_version_impl)

create-version-tag:
	git pull
	git tag $$(uv version --short)
	git push origin $$(uv version --short)

upgrade-patch-beta-push-tag: upgrade-patch-beta create-version-tag

upgrade-patch-push-tag: upgrade-patch create-version-tag
upgrade-minor-push-tag: upgrade-minor create-version-tag
upgrade-major-push-tag: upgrade-major create-version-tag