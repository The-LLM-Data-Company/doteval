"""Per Criterion grader evaluates each criterion separately in parallel LLM calls."""

import asyncio
import json

from rubric.autograders import Autograder
from rubric.types import Criterion, CriterionReport, EvaluationReport, GenerateFn
from rubric.utils import parse_json_to_dict

DEFAULT_SYSTEM_PROMPT = """You are evaluating an output for a given query against a single criterion.

You will receive the output to evaluate, a single criterion to check, and a <criterion_type> field indicating if the criterion is positive or negative.

CRITERION TYPES:
The <criterion_type> field tells you whether this criterion describes something desirable (positive) or undesirable (negative). Your job is THE SAME for both types: determine if the thing described in the criterion is actually present in the output.

POSITIVE CRITERIA:
Positive criteria describe desired traits, requirements, or content that should be present.
- MET (criterion_status: "MET"): The output contains/satisfies the requirement
- UNMET (criterion_status: "UNMET"): The output does not contain/satisfy the requirement

NEGATIVE CRITERIA:
Negative criteria describe active errors or mistakes that the output is making.
- MET (criterion_status: "MET"): The output advocates, states, or recommends the problematic thing
- UNMET (criterion_status: "UNMET"): The output does NOT make this error, OR it mentions the thing only to warn against it or mention why it's wrong

Examples of what does NOT count as MET for negative criteria:
- "This is often misdiagnosed as X, but it's actually Y" → NOT stating it's X (UNMET)
- "Avoid doing X because..." → NOT recommending X (UNMET)
- "Unlike X, the correct approach is Y" → NOT advocating for X (UNMET)
- "A common mistake is thinking X" → NOT claiming X is correct (UNMET)

EVALUATION RULES:
- For numerical values: Check if they fall within specified ranges or match exactly as required.
- For factual claims: Verify the information is present and accurate, regardless of exact phrasing.
- For required elements: Confirm presence, counting precisely when numbers are specified.
- For exclusion requirements: Confirm that restricted content is absent.
- For length requirements: Carefully measure the number of words, characters, items, etc.
- Be strict about factual accuracy but flexible about wording.
- Accept semantically equivalent statements or implications where appropriate.
- Pay careful attention to negation, warnings, and contrasts.

CRITERION STATUS:
"criterion_status" has *nothing* to do with quality or correctness. It only means:
- "MET": The thing described in the criterion IS present/occurring in the output
- "UNMET": The thing described in the criterion IS NOT present/occurring in the output

Your response must be valid JSON with this exact format:

{
"criterion_status": "MET",
"explanation": "Brief explanation of why the criterion is or isn't present."
}

Examples:

Positive criterion: "States Q4 2023 base margin as 17.2%"
Output: "The Q4 2023 base margin was 17.2% before adjustments."
{
"criterion_status": "MET",
"explanation": "The output states Q4 2023 base margin as 17.2%, as required."
}

Negative criterion: "States that the patient has diabetes"
Output: "This patient does not have diabetes."
{
"criterion_status": "UNMET",
"explanation": "The output explicitly states the patient does NOT have diabetes, so this error is not present."
}

Return only raw JSON starting with {, no back-ticks, no 'json' prefix."""


class PerCriterionGrader(Autograder):
    """Concrete autograder that evaluates each criterion independently."""

    def __init__(self, generate_fn: GenerateFn, *, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        super().__init__(generate_fn=generate_fn)
        self.system_prompt = system_prompt

    async def _judge_single_criterion(
        self, criterion: Criterion, to_grade: str, query: str | None = None
    ) -> CriterionReport:
        criterion_type = "negative" if criterion.weight < 0 else "positive"
        query_text = f"<input>{query}</input>" if query else ""
        user_prompt = f"""<criterion_type>
{criterion_type}
</criterion_type>

<criterion>
{criterion.requirement}
</criterion>

{query_text}

<output>
{to_grade}
</output>"""

        try:
            response = await self.generate(
                system_prompt=self.system_prompt, user_prompt=user_prompt
            )

            result = parse_json_to_dict(response)

            explanation = result.get("explanation", "No explanation provided")

            criterion_status = result.get("criterion_status", "UNMET").upper()
            verdict = "MET" if criterion_status == "MET" else "UNMET"

            return CriterionReport(
                requirement=criterion.requirement,
                verdict=verdict,
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

    async def judge(
        self, to_grade: str, rubric: list[Criterion], query: str | None = None
    ) -> list[CriterionReport]:
        criterion_tasks = [
            self._judge_single_criterion(criterion, to_grade, query) for criterion in rubric
        ]
        return list(await asyncio.gather(*criterion_tasks))

    async def aggregate(self, judge_results: list[CriterionReport]) -> EvaluationReport:
        score = 0.0
        max_score = 1.0

        total_positive_weight = sum(max(0.0, report.weight) for report in judge_results)
        weighted_score_sum = sum(
            (1.0 if report.verdict == "MET" else 0.0) * report.weight for report in judge_results
        )

        if total_positive_weight > 0:
            raw_score = weighted_score_sum / total_positive_weight
            score = max(0.0, min(max_score, raw_score))

        return EvaluationReport(
            score=score,
            report=judge_results,
        )
