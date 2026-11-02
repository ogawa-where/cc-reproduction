from slugkit.slug import slugify


def test_accents_transliterated():
    assert slugify("Crème Brûlée") == "creme-brulee"
    assert slugify("naïve café") == "naive-cafe"


def test_uppercase_accents():
    assert slugify("Ångström Élan") == "angstrom-elan"


def test_remaining_non_ascii_is_separator():
    assert slugify("Zürich東京2024") == "zurich-2024"
