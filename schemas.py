"""Pydantic data models for the AI Translation & Quality Scoring Pipeline.

Defines strict type hints, validation rules, and schema contracts.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class TranslationInput(BaseModel):
    """Input payload for context-aware string translation."""

    key: str = Field(..., description="Unique UI key/identifier (e.g. ticket.button.open)")
    context: str = Field(..., description="Developer commentary explaining UI placement & intent")
    english: str = Field(..., description="Original English UI text")


class TranslationOutput(BaseModel):
    """Output model representing a context-aware UI translation result."""

    key: str = Field(..., description="Unique UI key matching input")
    english: str = Field(..., description="Original English text")
    translation: str = Field(..., description="Contextually adapted Spanish translation")
    confidence: Literal["High", "Medium", "Low"] = Field(
        default="High", description="Confidence rating of translation accuracy"
    )
    reasoning: str = Field(
        ..., description="Explanation of context interpretation and word choice"
    )


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown matching the 100-point rubric criteria."""

    contextual_accuracy: float = Field(
        ..., ge=0.0, le=40.0, description="Contextual Accuracy score (0-40)"
    )
    linguistic_quality: float = Field(
        ..., ge=0.0, le=30.0, description="Linguistic Quality & Grammar score (0-30)"
    )
    ui_appropriateness: float = Field(
        ..., ge=0.0, le=20.0, description="UI Appropriateness & Length score (0-20)"
    )
    consistency: float = Field(
        ..., ge=0.0, le=10.0, description="Terminology & Structural Consistency score (0-10)"
    )

    @property
    def total(self) -> float:
        """Calculate total sum score."""
        return (
            self.contextual_accuracy
            + self.linguistic_quality
            + self.ui_appropriateness
            + self.consistency
        )


class QualityEvaluationInput(BaseModel):
    """Input payload for translation quality evaluation."""

    key: str = Field(..., description="Unique UI key identifier")
    context: str = Field(..., description="Developer context explaining intent")
    english: str = Field(..., description="Original English text")
    translation: str = Field(..., description="Candidate translation to be evaluated")


class QualityEvaluationOutput(BaseModel):
    """Output model representing an explainable quality evaluation result."""

    key: str = Field(..., description="Unique UI key")
    english: str = Field(..., description="Original English text")
    translation: str = Field(..., description="Evaluated Spanish translation")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Total score out of 100")
    score_breakdown: ScoreBreakdown = Field(..., description="Detailed rubric breakdown")
    status: Literal["Passed", "Needs Review"] = Field(
        ..., description="Overall approval status ('Passed' if >= 70 else 'Needs Review')"
    )
    issues_found: List[str] = Field(
        default_factory=list, description="List of identified translation errors or deficiencies"
    )
    severity: Literal["Critical", "High", "Medium", "Low", "None"] = Field(
        default="None", description="Highest severity level of identified issues"
    )
    suggested_translation: str = Field(
        ..., description="Recommended corrected translation"
    )
    explanation: str = Field(
        ..., description="Summary explanation of evaluation score"
    )
    reasoning: str = Field(
        ..., description="In-depth audit reasoning based on context and rubric"
    )


class PipelineSummary(BaseModel):
    """Aggregated quality scoring and pipeline summary metrics."""

    total_translated: int = Field(..., ge=0, description="Total UI strings processed")
    passed_count: int = Field(..., ge=0, description="Number of translations scoring >= 70")
    needs_review_count: int = Field(..., ge=0, description="Number of translations scoring < 70")
    average_score: float = Field(..., ge=0.0, le=100.0, description="Mean score across all items")
    highest_score: float = Field(..., ge=0.0, le=100.0, description="Maximum score achieved")
    lowest_score: float = Field(..., ge=0.0, le=100.0, description="Minimum score achieved")
    pass_rate_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of items passing review"
    )
