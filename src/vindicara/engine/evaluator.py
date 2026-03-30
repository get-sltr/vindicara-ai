"""Core evaluation pipeline."""

from vindicara.config.constants import MAX_INPUT_LENGTH, MAX_OUTPUT_LENGTH
from vindicara.engine.policy import PolicyRegistry
from vindicara.sdk.exceptions import VindicaraValidationError
from vindicara.sdk.types import GuardResult


class Evaluator:
    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def evaluate(
        self,
        text: str,
        policy_id: str,
        max_length: int = MAX_OUTPUT_LENGTH,
    ) -> GuardResult:
        if not text:
            raise VindicaraValidationError("Text must not be empty")
        if len(text) > max_length:
            raise VindicaraValidationError(
                f"Text exceeds maximum length of {max_length} characters"
            )
        policy = self._registry.get(policy_id)
        return policy.evaluate(text)

    def evaluate_guard(
        self,
        input_text: str,
        output_text: str,
        policy_id: str,
    ) -> GuardResult:
        if not input_text and not output_text:
            raise VindicaraValidationError("At least one of input or output must be provided")
        results: list[GuardResult] = []
        if input_text:
            results.append(self.evaluate(input_text, policy_id, max_length=MAX_INPUT_LENGTH))
        if output_text:
            results.append(self.evaluate(output_text, policy_id, max_length=MAX_OUTPUT_LENGTH))
        blocked = [r for r in results if r.is_blocked]
        if blocked:
            return blocked[0]
        flagged = [r for r in results if r.verdict.value == "flagged"]
        if flagged:
            return flagged[0]
        return results[0]

    @classmethod
    def with_builtins(cls) -> "Evaluator":
        return cls(PolicyRegistry.with_builtins())
