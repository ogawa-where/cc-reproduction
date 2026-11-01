import os

from notes import cli


def test_add_and_list(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["add", "hello"]) == 0
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "hello" in out
