import pytest

from rubric.autograders import PerCriterionOneShotGrader


@pytest.mark.asyncio
async def test_per_criterion_one_shot_grader_class_integration(
    sample_rubric, sample_output, one_shot_generate_fn
):
    grader = PerCriterionOneShotGrader(generate_fn=one_shot_generate_fn)

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
async def test_per_criterion_one_shot_grader_handles_invalid_json(sample_rubric):
    async def bad_generate(system_prompt: str, user_prompt: str) -> str:
        return "not-json"

    grader = PerCriterionOneShotGrader(generate_fn=bad_generate)

    judge_results = await grader.judge(
        to_grade="Example submission",
        rubric=sample_rubric.rubric,
    )
    report = await grader.aggregate(judge_results)

    assert report.score == 0.0
    assert report.report is not None
    for criterion_report in report.report:
        assert criterion_report.verdict == "UNMET"
        assert "Error parsing judge response" in criterion_report.reason


@pytest.mark.asyncio
async def test_per_criterion_one_shot_grader_with_negative_criterion_unmet(sample_rubric):
    async def generate_with_issue(system_prompt: str, user_prompt: str) -> str:
        import json

        return json.dumps(
            {
                "criteria_evaluations": [
                    {"criterion_number": 1, "criterion_status": "MET", "explanation": "Test"},
                    {"criterion_number": 2, "criterion_status": "MET", "explanation": "Test"},
                    {"criterion_number": 3, "criterion_status": "MET", "explanation": "Test"},
                    {
                        "criterion_number": 4,
                        "criterion_status": "UNMET",
                        "explanation": "Error not present",
                    },
                ]
            }
        )

    grader = PerCriterionOneShotGrader(generate_fn=generate_with_issue)

    report = await sample_rubric.grade("Test", autograder=grader)

    assert report.score == pytest.approx(1.0)
    assert report.report is not None
    verdicts = [criterion.verdict for criterion in report.report]
    assert verdicts == ["MET", "MET", "MET", "UNMET"]
