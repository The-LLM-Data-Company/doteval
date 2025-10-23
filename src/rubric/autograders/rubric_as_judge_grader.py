"""Passes the entire rubric to the LLM for holistic scoring."""

from __future__ import annotations

import json

from rubric.autograders import Autograder
from rubric.types import Criterion, EvaluationReport, GenerateFn
from rubric.utils import parse_json_to_dict

DEFAULT_SYSTEM_PROMPT = """You are an expert evaluator. You will be given an output and a list \
of criteria to evaluate it against.
Your job is to evaluate the output holistically against all criteria and provide an \
overall score from 0-100 that considers the weights of each criterion.

Do NOT evaluate each criterion individually - instead, consider the output as a whole \
and how well it satisfies the overall requirements.

Respond ONLY with valid JSON in this exact format:
{
  "overall_score": <number 0-100>
}"""


class RubricAsJudgeGrader(Autograder):
    """Concrete autograder that requests a single holistic score from the model."""

    def __init__(self, generate_fn: GenerateFn, *, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        super().__init__(generate_fn=generate_fn)
        self.system_prompt = system_prompt

    async def judge(self, to_grade: str, rubric: list[Criterion]) -> float:
        criteria_lines = []
        for index, criterion in enumerate(rubric, start=1):
            criterion_type = (
                "NEGATIVE (should NOT)" if criterion.weight < 0 else "POSITIVE (should)"
            )
            criteria_lines.append(
                f"{index}. [{criterion_type}] (weight: {criterion.weight}) {criterion.requirement}"
            )

        criteria_text = "\n".join(criteria_lines)
        user_prompt = f"""Evaluate this output holistically against the following criteria:

{criteria_text}

Output to evaluate:
{to_grade}

Provide your evaluation as JSON only with just the overall score."""

        try:
            response = await self.generate(self.system_prompt, user_prompt)
            result = parse_json_to_dict(response)
            overall_score_raw = result.get("overall_score", 0)
            overall_score = float(overall_score_raw)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return 0.0

        return overall_score

    async def aggregate(self, judge_results: float) -> EvaluationReport:
        clamped_score = max(0.0, min(100.0, judge_results))
        return EvaluationReport(score=clamped_score, report=None)
