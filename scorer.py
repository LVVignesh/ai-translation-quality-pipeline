"""Translation quality scoring service for Voxiis.

Evaluates candidates against the 100-point rubric (Contextual Accuracy, Linguistic Quality,
UI Appropriateness, Consistency), returning explainable evaluations and summary statistics.
"""

from typing import List, Optional, Tuple
from pydantic import ValidationError
from claude_client import ClaudeClient, ClaudeClientError
from logger import logger
from prompts import SCORING_SYSTEM_PROMPT, SCORING_USER_PROMPT_TEMPLATE
from schemas import (
    PipelineSummary,
    QualityEvaluationInput,
    QualityEvaluationOutput,
    ScoreBreakdown,
)


class QualityScorerService:
    """Service layer responsible for translation quality evaluation and rubric scoring."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None) -> None:
        """Initialize the Quality Scorer service.

        Args:
            claude_client: Instance of ClaudeClient. If None, instantiates default.
        """
        self.client = claude_client or ClaudeClient()

    def evaluate_single(
        self, item: QualityEvaluationInput, api_key: Optional[str] = None
    ) -> QualityEvaluationOutput:
        """Evaluate a single translation candidate using the 100-point rubric.

        Args:
            item: QualityEvaluationInput containing key, context, english, and candidate translation.
            api_key: Optional dynamic Anthropic API key.

        Returns:
            Validated QualityEvaluationOutput model.

        Raises:
            ClaudeClientError: If evaluation fails or API key is invalid.
        """
        user_prompt = SCORING_USER_PROMPT_TEMPLATE.format(
            key=item.key,
            context=item.context,
            english=item.english,
            translation=item.translation,
        )

        raw_dict = self.client.generate_json_completion(
            system_prompt=SCORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            override_api_key=api_key,
            temperature=0.0,
        )

        try:
            # Pydantic automatic instantiation and schema validation
            return QualityEvaluationOutput(**raw_dict)
        except (ValidationError, Exception) as validation_err:
            logger.error(f"Schema validation issue for evaluation key '{item.key}': {validation_err}")
            
            # Fallback scoring mechanism: constructs valid output with default rubric defaults if LLM JSON structure deviates
            breakdown_dict = raw_dict.get("score_breakdown", {})
            breakdown = ScoreBreakdown(
                contextual_accuracy=float(breakdown_dict.get("contextual_accuracy", 20.0)),
                linguistic_quality=float(breakdown_dict.get("linguistic_quality", 20.0)),
                ui_appropriateness=float(breakdown_dict.get("ui_appropriateness", 15.0)),
                consistency=float(breakdown_dict.get("consistency", 5.0)),
            )
            overall_score = float(raw_dict.get("overall_score", breakdown.total))
            status = "Passed" if overall_score >= 70.0 else "Needs Review"

            return QualityEvaluationOutput(
                key=item.key,
                english=item.english,
                translation=item.translation,
                overall_score=overall_score,
                score_breakdown=breakdown,
                status=status,
                issues_found=raw_dict.get("issues_found", ["Schema deviation during evaluation"]),
                severity=raw_dict.get("severity", "Medium" if status == "Needs Review" else "None"),
                suggested_translation=raw_dict.get("suggested_translation", item.translation),
                explanation=raw_dict.get("explanation", "Evaluation completed with fallback schema handling."),
                reasoning=raw_dict.get("reasoning", "Detailed audit generated via fallback parser."),
            )

    def calculate_summary(self, evaluations: List[QualityEvaluationOutput]) -> PipelineSummary:
        """Calculate aggregate pipeline statistics across evaluations.

        Args:
            evaluations: List of completed QualityEvaluationOutput items.

        Returns:
            Calculated PipelineSummary metrics model.
        """
        if not evaluations:
            return PipelineSummary(
                total_translated=0,
                passed_count=0,
                needs_review_count=0,
                average_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
                pass_rate_percentage=0.0,
            )

        total = len(evaluations)
        passed = sum(1 for e in evaluations if e.status == "Passed")
        needs_review = sum(1 for e in evaluations if e.status == "Needs Review")
        scores = [e.overall_score for e in evaluations]
        avg_score = round(sum(scores) / total, 1)
        max_score = round(max(scores), 1)
        min_score = round(min(scores), 1)
        pass_rate = round((passed / total) * 100.0, 1)

        return PipelineSummary(
            total_translated=total,
            passed_count=passed,
            needs_review_count=needs_review,
            average_score=avg_score,
            highest_score=max_score,
            lowest_score=min_score,
            pass_rate_percentage=pass_rate,
        )

    def evaluate_batch(
        self, items: List[QualityEvaluationInput], api_key: Optional[str] = None
    ) -> Tuple[List[QualityEvaluationOutput], PipelineSummary]:
        """Evaluate a list of translation candidates sequentially.

        Args:
            items: List of QualityEvaluationInput candidate items.
            api_key: Optional dynamic Anthropic API key.

        Returns:
            Tuple of (List[QualityEvaluationOutput], PipelineSummary).
        """
        logger.info(f"Starting quality scoring evaluation for {len(items)} items...")
        evaluations: List[QualityEvaluationOutput] = []

        for idx, item in enumerate(items, start=1):
            logger.info(f"Evaluating item {idx}/{len(items)}: key='{item.key}'")
            try:
                eval_result = self.evaluate_single(item, api_key=api_key)
                evaluations.append(eval_result)
            except ClaudeClientError as err:
                logger.error(f"Failed to evaluate key '{item.key}': {err}")
                # Create a fallback failure evaluation item
                fallback_breakdown = ScoreBreakdown(
                    contextual_accuracy=0.0,
                    linguistic_quality=0.0,
                    ui_appropriateness=0.0,
                    consistency=0.0,
                )
                evaluations.append(
                    QualityEvaluationOutput(
                        key=item.key,
                        english=item.english,
                        translation=item.translation,
                        overall_score=0.0,
                        score_breakdown=fallback_breakdown,
                        status="Needs Review",
                        issues_found=[f"API Error during evaluation: {str(err)}"],
                        severity="Critical",
                        suggested_translation=item.translation,
                        explanation="Evaluation failed due to API connection error.",
                        reasoning=f"System error: {str(err)}",
                    )
                )

        summary = self.calculate_summary(evaluations)
        logger.info(f"Completed quality evaluation. Pass rate: {summary.pass_rate_percentage}%")
        return evaluations, summary
