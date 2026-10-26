import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run([sys.executable, "-m", "fileindex.report", *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh]


def test_report_counts_and_largest(tmp_path):
    root, out = str(tmp_path / "root"), str(tmp_path / "report.txt")
    write(os.path.join(root, "a.py"), "xx")
    write(os.path.join(root, "sub", "b.py"), "xxxxxx")
    write(os.path.join(root, "sub", "notes.txt"), "x")
    write(os.path.join(root, "Makefile"), "xxx")
    r = run(root, out)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [ln for ln in read_lines(out)]
    while lines and not lines[-1].strip():
        lines.pop()
    assert lines == ["(none) 1", "py 2", "txt 1", "", "largest: sub/b.py 6", "files: 4"]


def test_report_empty_root(tmp_path):
    root, out = str(tmp_path / "root"), str(tmp_path / "report.txt")
    os.makedirs(root)
    r = run(root, out)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [ln for ln in read_lines(out) if ln.strip()]
    assert lines == ["largest: none", "files: 0"]


def test_report_missing_root_exits_2(tmp_path):
    out = str(tmp_path / "report.txt")
    r = run(str(tmp_path / "missing"), out)
    assert r.returncode == 2
    assert not os.path.exists(out)
