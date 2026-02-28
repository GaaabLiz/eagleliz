
# == PROJECT VARIABLES ==
PYTHON_MAIN_PACKAGE = eagleliz

# == APPLICATIONS CONFIGURATION ==

# Define the list of EXEs to build
APPS_LIST := eagleliz

# Configuration for 'pyliz'
eagleliz_NAME := pyliz
eagleliz_MAIN := $(PYTHON_MAIN_PACKAGE)/core/cli.py
eagleliz_ICO := resources/logo.ico
eagleliz_ICNS := resources/logo_1024x1024_1024x1024.icns


# == FILES VARIABLES ==
FILE_PROJECT_TOML := pyproject.toml
FILE_PROJECT_PY_GENERATED := $(PYTHON_MAIN_PACKAGE)/project.py