import pytest
from src.data_generator.clabe import clabe_check_digit, validate_clabe, generate_clabe

def test_check_digit():
    assert clabe_check_digit("03218000011835971") == 9
    assert clabe_check_digit("01218000123456789") == 9
def test_check_digit_length():
    with pytest.raises(ValueError):
        clabe_check_digit("1234")

def test_validate_good_clabe():
    assert validate_clabe("032180000118359719") is True

def test_validate_rejects_bad_digit():
    assert validate_clabe("032180000118359718") is False

def test_generate_clabe_and_validate():
    clabe = generate_clabe("012", "180", "12345678")
    assert validate_clabe(clabe) is True