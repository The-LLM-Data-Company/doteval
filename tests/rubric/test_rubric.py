import pytest

from rubric import Criterion, Rubric
from rubric.autograders import PerCriterionGrader

MOCK_DATASET = [
    {
        "input": "What is 2+2?",
        "output": "The answer is 4.",
        "expected": "4",
    },
    {
        "input": "What is the capital of France?",
        "output": "Paris is the capital of France.",
        "expected": "Paris",
    },
    {
        "input": "List three primary colors",
        "output": "Red, blue, and yellow are the three primary colors.",
        "expected": "red, blue, yellow",
    },
]


@pytest.mark.asyncio
async def test_rubric(per_criterion_generate_fn):
    formatting_criteria = [
        Criterion(
            weight=1.0,
            requirement="Output uses proper capitalization and punctuation",
        ),
        Criterion(
            weight=1.0,
            requirement="Output is concise and avoids unnecessary verbosity",
        ),
    ]

    formatting_rubric = Rubric(formatting_criteria)

    autograder = PerCriterionGrader(generate_fn=per_criterion_generate_fn)

    for idx, dataset_item in enumerate(MOCK_DATASET):
        correctness_criteria = [
            Criterion(
                weight=2.0,
                requirement=f"Output correctly answers the question: '{dataset_item['input']}'",
            ),
            Criterion(
                weight=1.0,
                requirement=(
                    f"Output includes the expected information: '{dataset_item['expected']}'"
                ),
            ),
        ]

        correctness_rubric = Rubric(correctness_criteria)

        correctness_report = await correctness_rubric.grade(
            dataset_item["output"],
            autograder=autograder,
        )

        formatting_report = await formatting_rubric.grade(
            dataset_item["output"],
            autograder=autograder,
        )

        assert correctness_report is not None, f"Item {idx + 1}: Correctness report is None"
        assert formatting_report is not None, f"Item {idx + 1}: Formatting report is None"

        assert 0 <= correctness_report.score <= 100, (
            f"Item {idx + 1}: Correctness score {correctness_report.score} out of range"
        )
        assert 0 <= formatting_report.score <= 100, (
            f"Item {idx + 1}: Formatting score {formatting_report.score} out of range"
        )

        assert correctness_report.report is not None, f"Item {idx + 1}: Correctness report is None"
        assert formatting_report.report is not None, f"Item {idx + 1}: Formatting report is None"

        assert len(correctness_report.report) == len(correctness_criteria), (
            f"Item {idx + 1}: Wrong number of correctness criteria"
        )

        assert len(formatting_report.report) == len(formatting_criteria), (
            f"Item {idx + 1}: Wrong number of formatting criteria"
        )

        for criterion in correctness_report.report:
            assert criterion.verdict in ["MET", "UNMET"], (
                f"Item {idx + 1}: Invalid correctness verdict {criterion.verdict}"
            )
            assert criterion.reason, f"Item {idx + 1}: Missing reason for correctness criterion"

        for criterion in formatting_report.report:
            assert criterion.verdict in ["MET", "UNMET"], (
                f"Item {idx + 1}: Invalid formatting verdict {criterion.verdict}"
            )
            assert criterion.reason, f"Item {idx + 1}: Missing reason for formatting criterion"
