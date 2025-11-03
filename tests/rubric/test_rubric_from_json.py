import json

import pytest

from rubric import Rubric

VALID_CRITERIA = [
    {"weight": 1.0, "requirement": "First requirement"},
    {"weight": 2.0, "requirement": "Second requirement"},
]


def test_from_json_string():
    json_string = json.dumps(VALID_CRITERIA)
    rubric = Rubric.from_json(json_string)
    assert len(rubric.rubric) == 2
    assert rubric.rubric[0].weight == 1.0
    assert rubric.rubric[1].weight == 2.0


def test_from_json_invalid_json():
    invalid_json = "{ invalid json content"
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_json(invalid_json)
    assert "Failed to parse JSON" in str(exc_info.value)


def test_from_json_invalid_criteria():
    json_string = json.dumps(
        [
            {"weight": 1.0, "requirement": "Valid criterion"},
            {"weight": "invalid_weight", "requirement": "Invalid criterion"},
        ]
    )
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_json(json_string)
    assert "Invalid criterion at index 1" in str(exc_info.value)


def test_from_json_empty_list():
    json_string = "[]"
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_json(json_string)
    assert "No criteria found" in str(exc_info.value)


def test_from_json_not_list():
    json_string = '{"weight": 1.0, "requirement": "test"}'
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_json(json_string)
    assert "Dict must contain either 'sections' or 'rubric' key" in str(exc_info.value)


def test_from_json_with_extra_fields():
    json_string = json.dumps(
        [
            {
                "weight": 1.0,
                "requirement": "Test requirement",
                "extra_field": "This should be ignored",
            }
        ]
    )
    rubric = Rubric.from_json(json_string)
    assert len(rubric.rubric) == 1
    assert rubric.rubric[0].weight == 1.0
