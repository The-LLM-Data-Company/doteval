import pytest

from rubric.autograders import PerCriterionGrader


@pytest.mark.asyncio
async def test_per_criterion_grader_class_integration(
    sample_rubric, sample_output, per_criterion_generate_fn
):
    grader = PerCriterionGrader(generate_fn=per_criterion_generate_fn)

    report = await sample_rubric.grade(sample_output, autograder=grader)

    assert report.score == pytest.approx(0.875)
    assert report.report is not None
    assert len(report.report) == len(sample_rubric.rubric)
    assert [criterion.verdict for criterion in report.report] == [
        "MET",
        "MET",
        "MET",
        "MET",
    ]


@pytest.mark.asyncio
async def test_per_criterion_grader_handles_invalid_json(sample_rubric):
    async def bad_generate(system_prompt: str, user_prompt: str) -> str:
        return "not-json"

    grader = PerCriterionGrader(generate_fn=bad_generate)

    report = await grader.grade(
        to_grade="Example submission",
        rubric=sample_rubric.rubric,
    )

    assert report.score == 0.0
    assert report.report is not None
    for criterion_report in report.report:
        assert criterion_report.verdict == "UNMET"
        assert "Error parsing judge response" in criterion_report.reason


@pytest.mark.asyncio
async def test_per_criterion_grader_with_negative_criterion_unmet(sample_rubric):
    async def generate_with_issue(system_prompt: str, user_prompt: str) -> str:
        import json
        import re

        criterion_type_match = re.search(
            r"<criterion_type>(.*?)</criterion_type>", user_prompt, re.DOTALL
        )
        criterion_type = (
            criterion_type_match.group(1).strip().lower() if criterion_type_match else "positive"
        )

        if criterion_type == "negative":
            # For negative criteria: criterion_status="UNMET" means the error is NOT present (good!)
            return json.dumps({"criterion_status": "UNMET", "explanation": "Error not present"})
        else:
            return json.dumps({"criterion_status": "MET", "explanation": "Requirement met"})

    grader = PerCriterionGrader(generate_fn=generate_with_issue)

    report = await sample_rubric.grade("Test", autograder=grader)

    assert report.score == pytest.approx(1.0)
    assert report.report is not None
    verdicts = [criterion.verdict for criterion in report.report]
    assert verdicts == ["MET", "MET", "MET", "UNMET"]
