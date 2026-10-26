import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run([sys.executable, "-m", "notify.digest", *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def test_digest_counts_kinds_and_skips_bad_lines(tmp_path):
    src, out = str(tmp_path / "events.log"), str(tmp_path / "digest.txt")
    write(src, "error|disk full\n\nwarning|hot\nbroken line\nerror|again\nbogus|unknown kind\n")
    r = run(src, out)
    assert r.returncode == 0, r.stdout + r.stderr
    with open(out, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    assert lines == ["ERROR: 2", "WARNING: 1", "total: 3"]
    combined = r.stdout + r.stderr
    assert "4" in combined  # the skipped line number is reported
    assert "3" in combined  # the count is reported


def test_digest_missing_input_exits_2_without_output(tmp_path):
    out = str(tmp_path / "digest.txt")
    r = run(str(tmp_path / "missing.log"), out)
    assert r.returncode == 2
    assert not os.path.exists(out)


def test_digest_function_raises_for_missing_input(tmp_path):
    import importlib

    mod = importlib.import_module("notify.digest")
    fn = next(getattr(mod, n) for n in dir(mod)
              if n.startswith("digest") and callable(getattr(mod, n)))
    try:
        fn(str(tmp_path / "missing.log"), str(tmp_path / "out.txt"))
    except Exception:  # noqa: BLE001 - any catchable error is acceptable
        return
    raise AssertionError("expected an error for a missing input file")
