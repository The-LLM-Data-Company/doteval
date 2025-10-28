"""Per Criterion grader evaluates each criterion separately in parallel LLM calls."""

import asyncio
import json

from rubric.autograders import Autograder
from rubric.types import Criterion, CriterionReport, EvaluationReport, GenerateFn
from rubric.utils import parse_json_to_dict

DEFAULT_SYSTEM_PROMPT = """You are evaluating whether a specific criterion is present in the \
provided output. 

IMPORTANT: The <criterion_type> field tells you whether this criterion describes something \
desirable (positive) or undesirable (negative), but your job is THE SAME for both types: \
determine if the thing described in the criterion IS ACTUALLY PRESENT in the output.

"criterion_status" has NOTHING to do with quality or correctness. It only means:
- "MET": The thing described in the criterion IS present/occurring in the output
- "UNMET": The thing described in the criterion IS NOT present/occurring in the output

CRITICAL DISTINCTION FOR NEGATIVE CRITERIA:
Negative criteria describe ACTIVE ERRORS or MISTAKES that the output is making. You must \
distinguish between:
- MET (criterion_status: "MET"): The output ADVOCATES, STATES, or RECOMMENDS the problematic thing
- UNMET (criterion_status: "UNMET"): The output does NOT make this error, OR it mentions the thing \
only to WARN AGAINST it, CONTRAST with it, or explain why it's WRONG

Examples of what does NOT count as MET for negative criteria:
- "This is often misdiagnosed as X, but it's actually Y" → NOT stating it's X (UNMET)
- "Avoid doing X because..." → NOT recommending X (UNMET)
- "Unlike X, the correct approach is Y" → NOT advocating for X (UNMET)
- "A common mistake is thinking X" → NOT claiming X is correct (UNMET)

Evaluation rules:
- For numerical values: Check if they fall within specified ranges or match exactly as required.
- For factual claims: Verify the information is present and accurate, regardless of exact phrasing.
- For required elements: Confirm presence, counting precisely when numbers are specified.
- For exclusion requirements: Confirm that restricted content is absent.
- For length requirements: Carefully measure the number of words, characters, items, etc.
- Be strict about factual accuracy but flexible about wording.
- Accept semantically equivalent statements or implications where appropriate.
- Pay careful attention to negation, warnings, and contrasts.

Your response must be valid JSON with this exact format (regardless of criterion type):

{
"criterion_status": "MET",
"explanation": "Brief explanation of why the criterion is or isn't present."
}

Examples:

Positive criterion: "Includes a summary of Q2 performance"
{
"criterion_status": "MET",
"explanation": "The output includes a clear summary of Q2 performance, as required."
}

Negative criterion: "States that the patient has diabetes"
Output: "This patient does not have diabetes."
{
"criterion_status": "UNMET",
"explanation": "The output explicitly states the patient does NOT have diabetes, so this error is not present."
}

Negative criterion: "Recommends ignoring safety protocols"
Output: "A common mistake is ignoring safety protocols, which can lead to accidents."
{
"criterion_status": "UNMET",
"explanation": "The output warns against ignoring safety protocols rather than recommending it, so this error is not present."
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

            # Use unified criterion_status field for both positive and negative criteria
            status = result.get("criterion_status", "UNMET")
            explanation = result.get("explanation", "No explanation provided")

            # Normalize to uppercase and check if it's MET
            verdict = "MET" if status.upper() == "MET" else "UNMET"

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
