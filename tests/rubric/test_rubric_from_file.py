import io
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from rubric import Rubric

VALID_CRITERIA = [
    {"weight": 1.0, "requirement": "First requirement"},
    {"weight": 2.0, "requirement": "Second requirement"},
]


def test_from_file_yaml_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(VALID_CRITERIA, f)
        temp_path = f.name

    try:
        rubric = Rubric.from_file(temp_path)
        assert len(rubric.rubric) == 2
        assert rubric.rubric[0].weight == 1.0
    finally:
        Path(temp_path).unlink()


def test_from_file_yml_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(VALID_CRITERIA, f)
        temp_path = f.name

    try:
        rubric = Rubric.from_file(temp_path)
        assert len(rubric.rubric) == 2
        assert rubric.rubric[0].weight == 1.0
    finally:
        Path(temp_path).unlink()


def test_from_file_json_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(VALID_CRITERIA, f)
        temp_path = f.name

    try:
        rubric = Rubric.from_file(temp_path)
        assert len(rubric.rubric) == 2
        assert rubric.rubric[0].weight == 1.0
    finally:
        Path(temp_path).unlink()


def test_from_file_yaml_file_object():
    yaml_content = yaml.dump(VALID_CRITERIA)
    file_obj = io.StringIO(yaml_content)
    file_obj.name = "test.yaml"

    rubric = Rubric.from_file(file_obj)
    assert len(rubric.rubric) == 2
    assert rubric.rubric[0].weight == 1.0


def test_from_file_json_file_object():
    json_content = json.dumps(VALID_CRITERIA)
    file_obj = io.StringIO(json_content)
    file_obj.name = "test.json"

    rubric = Rubric.from_file(file_obj)
    assert len(rubric.rubric) == 2
    assert rubric.rubric[0].weight == 1.0


def test_from_file_object_without_name():
    yaml_content = yaml.dump(VALID_CRITERIA)
    file_obj = io.StringIO(yaml_content)

    with pytest.raises(ValueError) as exc_info:
        Rubric.from_file(file_obj)
    assert "Cannot determine file format" in str(exc_info.value)
    assert "name" in str(exc_info.value)


def test_from_file_not_found():
    with pytest.raises(FileNotFoundError) as exc_info:
        Rubric.from_file("/nonexistent/path/to/rubric.yaml")
    assert "File not found" in str(exc_info.value)


def test_from_file_unsupported_extension():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test")
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            Rubric.from_file(temp_path)
        assert "Unsupported file format" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
        assert "Supported formats" in str(exc_info.value)
    finally:
        Path(temp_path).unlink()


def test_from_file_no_extension():
    with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
        f.write("test")
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            Rubric.from_file(temp_path)
        assert "Unsupported file format" in str(exc_info.value)
    finally:
        Path(temp_path).unlink()


def test_from_file_object_unsupported_extension():
    yaml_content = yaml.dump(VALID_CRITERIA)
    file_obj = io.StringIO(yaml_content)
    file_obj.name = "test.txt"

    with pytest.raises(ValueError) as exc_info:
        Rubric.from_file(file_obj)
    assert "Unsupported file format" in str(exc_info.value)
    assert ".txt" in str(exc_info.value)
