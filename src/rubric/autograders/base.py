"""Shared abstractions for autograder implementations."""

from abc import ABC, abstractmethod
from typing import Any

from rubric.types import Criterion, EvaluationReport, GenerateFn


class Autograder(ABC):
    """Base class describing the LLM-backed grading workflow.

    Subclasses inherit a ready-to-use `generate()` helper that delegates to the caller-supplied
    `generate_fn`. This keeps the LLM client choice outside of the core grading logic while making
    the dependency visible in constructors.
    """

    def __init__(self, generate_fn: GenerateFn | None = None):
        self.generate_fn: GenerateFn | None = generate_fn

    async def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Invoke the injected LLM callable with explicit system/user prompts."""
        if self.generate_fn is None:
            raise ValueError("generate_fn must be provided or override the generate method")
        return await self.generate_fn(system_prompt, user_prompt, **kwargs)

    @abstractmethod
    async def judge(self, to_grade: str, rubric: list[Criterion], query: str | None = None) -> Any:
        """Collect raw judge results for the provided submission."""
        pass

    @abstractmethod
    async def aggregate(self, judge_results: Any) -> EvaluationReport:
        """Transform judge results into an EvaluationReport."""
        pass

    async def grade(
        self, to_grade: str, rubric: list[Criterion], query: str | None = None
    ) -> EvaluationReport:
        """Grade the submission against the rubric. This is the main entry point for the autograder.
        You can override this method to implement custom grading logic outside the judge and
        aggregate steps.
        """

        judge_results = await self.judge(to_grade, rubric, query)
        return await self.aggregate(judge_results)
