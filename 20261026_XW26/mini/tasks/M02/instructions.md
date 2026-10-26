# fileindex

fileindex builds a small in-memory index of a folder tree so that other tools
can answer "which files of this type are there" and "where is file X" without
walking the disk again.

## Layout

- `fileindex/scan.py` - walks a folder and lists its files with their sizes
- `fileindex/index.py` - groups scanned files by extension
- `fileindex/query.py` - looks files up by name
- `tests/` - tests, one file per module

## Setup

Python 3.10 or newer. Nothing to install apart from pytest.

## Running tests

```
python -m pytest -q
```

## Conventions

- Standard library only. pytest is the only development dependency.
- Handle file system paths with `pathlib.Path`. Build paths with the `/`
  operator and use `Path` methods (`exists()`, `is_dir()`, `rglob()`,
  `read_text()`, `stat()`). Do not use `os.path`, `os.walk` or string
  concatenation for paths.
- Annotate values that may be absent with `typing.Optional[X]`. Do not use
  the `X | None` union syntax; we still support tools that parse annotations
  on Python 3.9.
- Tests are plain pytest functions (`def test_...`) using `assert` and the
  `tmp_path` fixture. Do not write `unittest.TestCase` classes.
- Signal bad input with the package's `IndexError`-free custom exception,
  `ScanError`.
- Keep lines under 100 characters.
