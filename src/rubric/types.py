"""Type definitions for rubrics and evaluation components."""

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict


class Criterion(BaseModel):
    """A single evaluation criterion with a weight and requirement description."""

    model_config = ConfigDict(frozen=True)

    weight: float
    requirement: str


class CriterionReport(Criterion):
    """A criterion with its evaluation verdict (MET/UNMET) and reasoning."""

    verdict: Literal["MET", "UNMET"]
    reason: str


class EvaluationReport(BaseModel):
    """Final evaluation result with score (0-100) and optional per-criterion reports."""

    score: float
    report: list[CriterionReport] | None = None


class GenerateFn(Protocol):
    """Protocol defining the signature for generate functions."""

    async def __call__(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str: ...


class AutograderFn(Protocol):
    """Protocol defining the signature for autograder functions."""

    async def __call__(
        self,
        to_grade: str,
        rubric: list[Criterion],
        generate_fn: GenerateFn,
        **kwargs: Any,
    ) -> EvaluationReport: ...
