import pytest
import yaml

from rubric import Rubric

VALID_CRITERIA = [
    {"weight": 1.0, "requirement": "First requirement"},
    {"weight": 2.0, "requirement": "Second requirement"},
]


def test_from_yaml_string():
    yaml_string = """
- weight: 1.0
  requirement: First requirement
- weight: 2.0
  requirement: Second requirement
"""
    rubric = Rubric.from_yaml(yaml_string)
    assert len(rubric.rubric) == 2
    assert rubric.rubric[0].weight == 1.0
    assert rubric.rubric[1].weight == 2.0


def test_from_yaml_invalid_yaml():
    invalid_yaml = "{ invalid: yaml: content"
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_yaml(invalid_yaml)
    assert "Failed to parse YAML" in str(exc_info.value)


def test_from_yaml_invalid_criteria():
    yaml_string = """
- weight: 1.0
  requirement: Valid criterion
- weight: invalid_weight
  requirement: Invalid criterion
"""
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_yaml(yaml_string)
    assert "Invalid criterion at index 1" in str(exc_info.value)


def test_from_yaml_empty_list():
    yaml_string = "[]"
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_yaml(yaml_string)
    assert "No criteria found" in str(exc_info.value)


def test_from_yaml_not_list():
    yaml_string = "weight: 1.0\nrequirement: test"
    with pytest.raises(ValueError) as exc_info:
        Rubric.from_yaml(yaml_string)
    assert "Dict must contain either 'sections' or 'rubric' key" in str(exc_info.value)


def test_from_yaml_with_extra_fields():
    yaml_string = """
- weight: 1.0
  requirement: Test requirement
  extra_field: This should be ignored
"""
    rubric = Rubric.from_yaml(yaml_string)
    assert len(rubric.rubric) == 1
    assert rubric.rubric[0].weight == 1.0


def test_from_yaml_multiple_criteria():
    criteria = [{"weight": float(i), "requirement": f"Requirement {i}"} for i in range(1, 11)]
    yaml_string = yaml.dump(criteria)
    rubric = Rubric.from_yaml(yaml_string)
    assert len(rubric.rubric) == 10
    for i, criterion in enumerate(rubric.rubric, 1):
        assert criterion.weight == float(i)
        assert criterion.requirement == f"Requirement {i}"
