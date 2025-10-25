import pytest

from rubric.autograders import RubricAsJudgeGrader


@pytest.mark.asyncio
async def test_rubric_as_judge_grader_class_integration(
    sample_rubric, sample_output, rubric_as_judge_generate_fn
):
    grader = RubricAsJudgeGrader(generate_fn=rubric_as_judge_generate_fn)

    report = await sample_rubric.grade(sample_output, autograder=grader)

    assert report.score == pytest.approx(0.85)
    assert report.report is None


@pytest.mark.asyncio
async def test_rubric_as_judge_grader_handles_invalid_json(sample_rubric):
    async def bad_generate(system_prompt: str, user_prompt: str) -> str:
        return "not-json"

    grader = RubricAsJudgeGrader(generate_fn=bad_generate)

    score = await grader.judge(
        to_grade="Example submission",
        rubric=sample_rubric.rubric,
    )
    assert score == 0.0

    report = await grader.aggregate(score)
    assert report.score == 0.0
    assert report.report is None
