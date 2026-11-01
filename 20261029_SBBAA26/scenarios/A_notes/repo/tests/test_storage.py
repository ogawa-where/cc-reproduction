from notes import storage


def test_add_assigns_incrementing_ids(tmp_path):
    notes = []
    a = storage.add(notes, "a")
    b = storage.add(notes, "b")
    assert (a["id"], b["id"]) == (1, 2)
    storage.save(notes, tmp_path / "n.json")
    assert storage.load(tmp_path / "n.json") == notes


def test_get_missing_raises():
    try:
        storage.get([], 9)
    except KeyError:
        return
    raise AssertionError
