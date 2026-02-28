#    $$\      $$\  $$$$$$\  $$\   $$\ $$$$$$$$\ $$$$$$$$\ $$$$$$\ $$\       $$$$$$$$\
#    $$$\    $$$ |$$  __$$\ $$ | $$  |$$  _____|$$  _____|\_$$  _|$$ |      $$  _____|
#    $$$$\  $$$$ |$$ /  $$ |$$ |$$  / $$ |      $$ |        $$ |  $$ |      $$ |
#    $$\$$\$$ $$ |$$$$$$$$ |$$$$$  /  $$$$$\    $$$$$\      $$ |  $$ |      $$$$$\
#    $$ \$$$  $$ |$$  __$$ |$$  $$<   $$  __|   $$  __|     $$ |  $$ |      $$  __|
#    $$ |\$  /$$ |$$ |  $$ |$$ |\$$\  $$ |      $$ |        $$ |  $$ |      $$ |
#    $$ | \_/ $$ |$$ |  $$ |$$ | \$$\ $$$$$$$$\ $$ |      $$$$$$\ $$$$$$$$\ $$$$$$$$\
#    \__|     \__|\__|  \__|\__|  \__|\________|\__|      \______|\________|\________|
#
#                                   VERSION 1.0.1

include project.mk





#      ______ _   ___      _______ _____   ____  __  __ ______ _   _ _______
#     |  ____| \ | \ \    / /_   _|  __ \ / __ \|  \/  |  ____| \ | |__   __|
#     | |__  |  \| |\ \  / /  | | | |__) | |  | | \  / | |__  |  \| |  | |
#     |  __| | . ` | \ \/ /   | | |  _  /| |  | | |\/| |  __| | . ` |  | |
#     | |____| |\  |  \  /   _| |_| | \ \| |__| | |  | | |____| |\  |  | |
#     |______|_| \_|   \/   |_____|_|  \_\\____/|_|  |_|______|_| \_|  |_|

# Rule to create a virtual environment and install dependencies
install-env:
	uv sync
	uv sync --all-extras





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
	- rm -rf $(PYTHON_MAIN_PACKAGE).spec

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
	pyliz gen-project-py $(FILE_PROJECT_TOML) $(FILE_PROJECT_PY_GENERATED)

gen-qt-res-py:
	$(QT_COMMAND_GEN_RES) $(QT_QRC_FILE) -o $(QT_RESOURCE_PY); \

installer:
	ISCC.exe $(INNO_SETUP_FILE)

build-uv:
	uv build

build-exe:
	uv run pyinstaller --windowed --icon=$(FILE_MAIN_LOGO_ICO) --name=$(APP_NAME) $(FILE_MAIN)

docs-gen:
	pdoc -o docs -d markdown $(PYTHON_MAIN_PACKAGE)

build-app: clean gen-project-py build-uv build-exe

build-installer: build-app installer





#     __      _______  _____
#     \ \    / / ____|/ ____|
#      \ \  / / |    | (___
#       \ \/ /| |     \___ \
#        \  / | |____ ____) |
#         \/   \_____|_____/
#
#

upgrade-patch:
	uv version --bump patch
	pyliz gen-project-py $(FILE_PROJECT_TOML) $(FILE_PROJECT_PY_GENERATED)
	@VERSION=$$(uv version --short); \
	if [ -f $(INNO_SETUP_FILE) ]; then \
		echo "Inno setup script found. upgrading version to $$VERSION..."; \
		sed -i "s/#define $(INNO_SETUP_VERSION_VARIABLE) \"[^\"]*\"/#define $(INNO_SETUP_VERSION_VARIABLE) \"$$VERSION\"/" $(INNO_SETUP_FILE); \
	fi; \
	git commit -am "bump: Bump version to $$VERSION"; \
	git push


upgrade-patch-push-tag: upgrade-patch
	git pull
	git tag $$(uv version --short)
	git push origin $$(uv version --short)