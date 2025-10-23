"""Autograder that evaluates all criteria in a single LLM call."""

from __future__ import annotations

import json

from rubric.autograders import Autograder
from rubric.types import Criterion, CriterionReport, EvaluationReport, GenerateFn
from rubric.utils import parse_json_to_dict

DEFAULT_SYSTEM_PROMPT = """You are an expert evaluator. You will be given an output and a list \
of criteria to evaluate it against.
Your job is to evaluate each criterion individually and determine if it is MET or UNMET.

For each criterion, provide:
- A verdict (MET or UNMET)
- A brief explanation of why

Do NOT provide an overall score - only evaluate each criterion.

Respond ONLY with valid JSON in this exact format:
{
  "criteria_evaluations": [
    {
      "criterion_number": 1,
      "verdict": "MET" or "UNMET",
      "reason": "Brief explanation"
    },
    ...
  ]
}"""


class PerCriterionOneShotGrader(Autograder):
    """Concrete autograder that judges every criterion within a single LLM response."""

    def __init__(self, generate_fn: GenerateFn, *, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        super().__init__(generate_fn=generate_fn)
        self.system_prompt = system_prompt

    async def judge(self, to_grade: str, rubric: list[Criterion]) -> list[CriterionReport]:
        criteria_lines = []
        for index, criterion in enumerate(rubric, start=1):
            criterion_type = (
                "NEGATIVE (should NOT)" if criterion.weight < 0 else "POSITIVE (should)"
            )
            criteria_lines.append(
                f"{index}. [{criterion_type}] (weight: {criterion.weight}) {criterion.requirement}"
            )

        criteria_text = "\n".join(criteria_lines)
        user_prompt = f"""Evaluate this output against the following criteria:

{criteria_text}

Output to evaluate:
{to_grade}

Provide your evaluation as JSON only."""

        try:
            response = await self.generate(self.system_prompt, user_prompt)
            result = parse_json_to_dict(response)
            evaluations = result.get("criteria_evaluations", [])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return [
                CriterionReport(
                    requirement=criterion.requirement,
                    verdict="UNMET",
                    reason=f"Error parsing judge response: {error}",
                    weight=criterion.weight,
                )
                for criterion in rubric
            ]

        criterion_reports: list[CriterionReport] = []
        for index, criterion in enumerate(rubric, start=1):
            eval_data = next(
                (entry for entry in evaluations if entry.get("criterion_number") == index),
                None,
            )

            if eval_data:
                verdict_raw = str(eval_data.get("verdict", "")).strip().upper()
                verdict = "MET" if verdict_raw == "MET" else "UNMET"
                reason = str(eval_data.get("reason", "No reason provided"))
            else:
                verdict = "UNMET"
                reason = "Evaluation not found in response"

            criterion_reports.append(
                CriterionReport(
                    requirement=criterion.requirement,
                    verdict=verdict,
                    reason=reason,
                    weight=criterion.weight,
                )
            )

        return criterion_reports

    async def aggregate(self, judge_results: list[CriterionReport]) -> EvaluationReport:
        total_positive_weight = sum(max(0.0, report.weight) for report in judge_results)
        weighted_score_sum = sum(
            (1.0 if report.verdict == "MET" else 0.0) * report.weight for report in judge_results
        )

        score = 0.0
        if total_positive_weight > 0:
            raw_score = (100.0 * weighted_score_sum) / total_positive_weight
            score = max(0.0, min(100.0, raw_score))

        return EvaluationReport(score=score, report=judge_results)
