# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install into a virtualenv
make install

# Run all tests (requires network access for GitHub API and URL checks)
make test

# Run short tests (no GitHub API / long URL checks)
make test_short

# Run linter (non-blocking, min score 9.45)
make test_pylint

# Run a specific test target
make test_import_shaarli
make test_archive_webpages
make test_export_html_table

# Clean generated test artifacts
make clean
```

All `make` targets activate `.venv` internally, so `source .venv/bin/activate` is only needed for manual `hecat` CLI invocations.

## Architecture

hecat is a pipeline tool: a YAML config file (`.hecat.yml` by default) declares a list of `steps`, each specifying a `module` and `module_options`. `main.py` reads the config and dispatches each step to the matching function.

### Module dispatch (`hecat/main.py`)

Module names use `category/name` strings (e.g. `importers/markdown_awesome`). `main.py` maps these strings to imported functions via a chain of `if/elif` blocks. Adding a new module requires:
1. Implementing the function in the appropriate subpackage.
2. Importing it in the subpackage's `__init__.py`.
3. Adding the `elif` branch in `main.py`.

### Module categories

| Category | Location | Purpose |
|---|---|---|
| Importers | `hecat/importers/` | Read external formats → YAML data |
| Processors | `hecat/processors/` | Read and mutate YAML data in-place |
| Exporters | `hecat/exporters/` | Read YAML data → output files |

### YAML data model

- `load_yaml_data(path)` in `hecat/utils.py` handles both single files and directories (loads each `.yml` file as one list item).
- Writes are done atomically via a `.tmp` file then `os.rename` (`write_data_file` in `utils.py`).
- `ruamel.yaml` (round-trip mode) is used throughout to preserve YAML formatting.

### Test fixtures

Test config files live in `tests/` as `.hecat.*.yml`. Tests clone external repos (`tests/awesome-selfhosted`, `tests/awesome-selfhosted-data`) at test time; `make clone_awesome_selfhosted` fetches them separately.
