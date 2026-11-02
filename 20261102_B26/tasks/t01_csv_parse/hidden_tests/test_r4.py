import pytest

from csvlite.parser import parse_csv


def test_too_many_fields_raises():
    with pytest.raises(ValueError):
        parse_csv("a,b\n1,2,3")


def test_too_few_fields_raises():
    with pytest.raises(ValueError):
        parse_csv("a,b,c\n1,2,3\n4,5")
