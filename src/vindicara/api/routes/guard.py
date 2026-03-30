"""POST /v1/guard endpoint."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from vindicara.api.deps import get_evaluator
from vindicara.engine.evaluator import Evaluator
from vindicara.sdk.exceptions import VindicaraValidationError
from vindicara.sdk.types import GuardResult

logger = structlog.get_logger()

router = APIRouter(prefix="/v1")


class GuardRequest(BaseModel):
    input: str = ""
    output: str = ""
    policy: str = "content-safety"

    @model_validator(mode="after")
    def check_input_or_output(self) -> "GuardRequest":
        if not self.input and not self.output:
            raise ValueError("At least one of 'input' or 'output' must be provided")
        return self


@router.post("/guard", response_model=GuardResult)
async def guard(
    request: GuardRequest,
    evaluator: Evaluator = Depends(get_evaluator),
) -> GuardResult:
    evaluation_id = str(uuid.uuid4())
    log = logger.bind(evaluation_id=evaluation_id, policy=request.policy)
    log.info("guard.evaluation.started")

    try:
        result = evaluator.evaluate_guard(
            input_text=request.input,
            output_text=request.output,
            policy_id=request.policy,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=404, detail=f"Policy '{request.policy}' not found"
        ) from err
    except VindicaraValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    result.evaluation_id = evaluation_id
    log.info(
        "guard.evaluation.completed", verdict=result.verdict.value, latency_ms=result.latency_ms
    )
    return result
