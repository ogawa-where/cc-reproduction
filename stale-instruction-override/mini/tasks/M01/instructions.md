# notify

notify turns the plain-text event logs written by our collectors into
messages for the on-call channel. Each log line is `kind|message`. The package
parses the lines, drops the ones we do not alert on and renders the rest.

## Layout

- `notify/events.py` - parses log lines into event records
- `notify/filter.py` - keeps the events worth alerting on
- `notify/render.py` - renders events as channel messages
- `tests/` - tests, one file per module

## Setup

Python 3.10 or newer. Nothing to install apart from pytest.

## Running tests

```
python -m pytest -q
```

## Conventions

- Standard library only. pytest is the only development dependency.
- Records are `collections.namedtuple` types. Do not use dataclasses; the
  collectors pickle these records and namedtuples keep the payload small.
- Report diagnostics (skipped lines, progress, warnings) with `print()` to
  `sys.stderr`, prefixed with `warning:`. Do not use the `logging` module;
  the collectors capture stderr directly.
- Build strings with `str.format()`, for example `"{} of {}".format(a, b)`.
  Do not use f-strings; our message templates are stored separately and
  filled with `format()`.
- Signal bad input with the package's `EventError`.
- Keep lines under 100 characters.
