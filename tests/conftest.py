import json
import re
from collections.abc import Awaitable, Callable

import pytest
from dotenv import load_dotenv

from rubric import Criterion, Rubric

CriterionList = list[Criterion]
GenerateFn = Callable[[str, str], Awaitable[str]]

load_dotenv()


@pytest.fixture
def sample_output() -> str:
    return "Paris is the capital of France. It is a beautiful city with rich history."


@pytest.fixture
def sample_criteria() -> CriterionList:
    return [
        Criterion(
            weight=2.0,
            requirement="Output mentions Paris",
        ),
        Criterion(
            weight=1.0,
            requirement="Output mentions France",
        ),
        Criterion(
            weight=1.0,
            requirement="Output is written in complete sentences",
        ),
        Criterion(
            weight=-0.5,
            requirement="Output contains profanity or offensive language",
        ),
    ]


@pytest.fixture
def sample_rubric(sample_criteria: CriterionList) -> Rubric:
    return Rubric(sample_criteria)


def _extract_field(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        raise ValueError("Expected field not found in prompt")
    return match.group(1).strip()


@pytest.fixture
def per_criterion_generate_fn() -> GenerateFn:
    criterion_pattern = re.compile(r"<criterion>(.*?)</criterion>", re.DOTALL)
    type_pattern = re.compile(r"<criterion_type>(.*?)</criterion_type>", re.DOTALL)
    positive_requirements_met = {
        "Output mentions Paris",
        "Output mentions France",
        "Output is written in complete sentences",
    }
    negative_issue_present = {
        "Output contains profanity or offensive language": False,
    }

    async def _generate(system_prompt: str, user_prompt: str) -> str:
        criterion_text = _extract_field(criterion_pattern, user_prompt)
        criterion_type = _extract_field(type_pattern, user_prompt).lower()

        if criterion_type == "negative":
            issue_present = negative_issue_present.get(criterion_text, True)
            explanation = (
                "Detected disallowed content in the output."
                if issue_present
                else "No disallowed content found."
            )
            return json.dumps(
                {
                    "issue_present": issue_present,
                    "explanation": explanation,
                }
            )

        criteria_met = criterion_text in positive_requirements_met
        explanation = (
            "Requirement satisfied by the submission."
            if criteria_met
            else "Requirement not satisfied by the submission."
        )
        return json.dumps(
            {
                "criteria_met": criteria_met,
                "explanation": explanation,
            }
        )

    return _generate


@pytest.fixture
def one_shot_generate_fn(sample_criteria: CriterionList) -> GenerateFn:
    async def _generate(system_prompt: str, user_prompt: str) -> str:
        evaluations = []
        for index, criterion in enumerate(sample_criteria, start=1):
            if criterion.weight < 0:
                verdict = "MET"
                reason = "No disallowed content found in the submission."
            else:
                verdict = "MET"
                reason = "Requirement satisfied by the submission."
            evaluations.append(
                {
                    "criterion_number": index,
                    "verdict": verdict,
                    "reason": reason,
                }
            )

        return json.dumps({"criteria_evaluations": evaluations})

    return _generate


@pytest.fixture
def rubric_as_judge_generate_fn() -> GenerateFn:
    async def _generate(system_prompt: str, user_prompt: str) -> str:
        return json.dumps({"overall_score": 135.0})

    return _generate
