import pytest

from rubric import Rubric

VALID_CRITERIA = [
    {"weight": 1.0, "requirement": "First requirement"},
    {"weight": 2.0, "requirement": "Second requirement"},
]


def test_from_dict_valid():
    rubric = Rubric.from_dict(VALID_CRITERIA)
    assert len(rubric.rubric) == 2
    assert rubric.rubric[0].weight == 1.0
    assert rubric.rubric[0].requirement == "First requirement"
    assert rubric.rubric[1].weight == 2.0
    assert rubric.rubric[1].requirement == "Second requirement"


def test_from_dict_empty_list():
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict([])
    assert "No criteria found" in str(exc_info.value)


def test_from_dict_not_list():
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict({"weight": 1.0, "requirement": "test"})  # type: ignore
    assert "Expected a list of criteria" in str(exc_info.value)


def test_from_dict_missing_weight():
    invalid_data = [{"requirement": "Missing weight"}]
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict(invalid_data)
    assert "Invalid criterion at index 0" in str(exc_info.value)
    assert "weight" in str(exc_info.value).lower()


def test_from_dict_missing_requirement():
    invalid_data = [{"weight": 1.0}]
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict(invalid_data)
    assert "Invalid criterion at index 0" in str(exc_info.value)
    assert "requirement" in str(exc_info.value).lower()


def test_from_dict_invalid_weight_type():
    invalid_data = [{"weight": "invalid", "requirement": "test"}]
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict(invalid_data)
    assert "Invalid criterion at index 0" in str(exc_info.value)


def test_from_dict_item_not_dict():
    invalid_data = ["not a dict"]
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_dict(invalid_data)
    assert "Invalid criterion at index 0" in str(exc_info.value)
    assert "expected a dictionary" in str(exc_info.value)
