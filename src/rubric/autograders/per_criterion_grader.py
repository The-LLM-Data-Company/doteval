"""Per Criterion grader evaluates each criterion separately in parallel LLM calls."""

import asyncio
import json

from rubric.autograders import Autograder
from rubric.types import Criterion, CriterionReport, EvaluationReport, GenerateFn
from rubric.utils import parse_json_to_dict

DEFAULT_SYSTEM_PROMPT = """You are evaluating whether a specific criterion is true of the \
provided output. Each criterion describes either a desired trait (positive) or an \
undesired trait (negative). You will be told which via the <criterion_type> field.

Your task is to determine whether the criterion, as written, is satisfied (for positive \
criteria) or whether the issue described is present (for negative criteria) based on the \
full output provided. Do not make any value judgements about the quality or usefulness \
of the output — only evaluate literal truth.

Evaluation rules:
- For numerical values: Check if they fall within specified ranges or match exactly as required.
- For factual claims: Verify the information is present and accurate, regardless of exact phrasing.
- For required elements: Confirm presence, counting precisely when numbers are specified.
- For exclusion requirements: Confirm that restricted content is absent.
- For length requirements: Carefully measure the number of words, characters, items, etc.
- Be strict about factual accuracy but flexible about wording.
- Accept semantically equivalent statements or implications where appropriate.

Your response must be valid JSON:

If <criterion_type> is "positive":
- Return "criteria_met": true if the requirement is fully satisfied.
- Return "criteria_met": false if the requirement is not satisfied.

If <criterion_type> is "negative":
- Return "issue_present": true if the issue is present in the output.
- Return "issue_present": false if the issue is absent.

Always include a concise explanation justifying your answer.

Examples:

Positive criterion:
{
"criteria_met": true,
"explanation": "The output includes a clear summary of Q2 performance, as required."
}

Negative criterion:
{
"issue_present": true,
"explanation": "The output includes an 8-K filing dated April 2023, which falls within the \
restricted range."
}

Return only raw JSON starting with {, no back-ticks, no 'json' prefix."""


class PerCriterionGrader(Autograder):
    """Concrete autograder that evaluates each criterion independently."""

    def __init__(self, generate_fn: GenerateFn, *, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        super().__init__(generate_fn=generate_fn)
        self.system_prompt = system_prompt

    async def _judge_single_criterion(self, criterion: Criterion, to_grade: str) -> CriterionReport:
        criterion_type = "negative" if criterion.weight < 0 else "positive"
        user_prompt = f"""<criterion_type>{criterion_type}</criterion_type>

<criterion>
{criterion.requirement}
</criterion>

<output>
{to_grade}
</output>"""

        try:
            response = await self.generate(
                system_prompt=self.system_prompt, user_prompt=user_prompt
            )

            result = parse_json_to_dict(response)

            if criterion_type == "negative":
                passed = not result.get("issue_present", True)
                explanation = result.get("explanation", "No explanation provided")
            else:
                passed = result.get("criteria_met", False)
                explanation = result.get("explanation", "No explanation provided")

            return CriterionReport(
                requirement=criterion.requirement,
                verdict="MET" if passed else "UNMET",
                reason=explanation,
                weight=criterion.weight,
            )

        except (json.JSONDecodeError, KeyError) as e:
            return CriterionReport(
                requirement=criterion.requirement,
                verdict="UNMET",
                reason=f"Error parsing judge response: {str(e)}",
                weight=criterion.weight,
            )

    async def judge(self, to_grade: str, rubric: list[Criterion]) -> list[CriterionReport]:
        criterion_tasks = [
            self._judge_single_criterion(criterion, to_grade) for criterion in rubric
        ]
        return list(await asyncio.gather(*criterion_tasks))

    async def aggregate(self, judge_results: list[CriterionReport]) -> EvaluationReport:
        score = 0.0
        max_score = 100.0

        total_positive_weight = sum(max(0.0, report.weight) for report in judge_results)
        weighted_score_sum = sum(
            (1.0 if report.verdict == "MET" else 0.0) * report.weight for report in judge_results
        )

        if total_positive_weight > 0:
            raw_score = (100.0 * weighted_score_sum) / total_positive_weight
            score = max(0.0, min(max_score, raw_score))

        return EvaluationReport(
            score=score,
            report=judge_results,
        )
