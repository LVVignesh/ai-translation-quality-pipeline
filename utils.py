"""Utility helpers for Voxiis AI Translation & Quality Scoring Pipeline.

Provides functions for converting Pydantic internal models to Pandas DataFrames for Gradio
table visualization, as well as file export utilities (CSV and JSON).
"""

import json
import tempfile
from typing import List, Sequence
import pandas as pd
from pydantic import BaseModel
from schemas import QualityEvaluationOutput, TranslationOutput


def translation_outputs_to_dataframe(results: List[TranslationOutput]) -> pd.DataFrame:
    """Convert a list of TranslationOutput Pydantic models to a Pandas DataFrame.

    Args:
        results: List of TranslationOutput objects.

    Returns:
        pd.DataFrame formatted for Gradio Table display.
    """
    if not results:
        return pd.DataFrame(
            columns=["Key", "English Text", "Spanish Translation", "Confidence", "Reasoning"]
        )

    records = []
    for item in results:
        records.append(
            {
                "Key": item.key,
                "English Text": item.english,
                "Spanish Translation": item.translation,
                "Confidence": item.confidence,
                "Reasoning": item.reasoning,
            }
        )

    return pd.DataFrame(records)


def quality_outputs_to_dataframe(results: List[QualityEvaluationOutput]) -> pd.DataFrame:
    """Convert a list of QualityEvaluationOutput models to a Pandas DataFrame.

    Args:
        results: List of QualityEvaluationOutput objects.

    Returns:
        pd.DataFrame formatted for Gradio Table display.
    """
    if not results:
        return pd.DataFrame(
            columns=[
                "Key",
                "English",
                "Spanish",
                "Score",
                "Breakdown (Context/Ling/UI/Cons)",
                "Status",
                "Issues Found",
                "Severity",
                "Suggested Translation",
                "Explanation",
            ]
        )

    records = []
    for item in results:
        b = item.score_breakdown
        breakdown_str = f"C:{b.contextual_accuracy:.0f}/40 | L:{b.linguistic_quality:.0f}/30 | UI:{b.ui_appropriateness:.0f}/20 | K:{b.consistency:.0f}/10"
        issues_str = ", ".join(item.issues_found) if item.issues_found else "None"

        records.append(
            {
                "Key": item.key,
                "English": item.english,
                "Spanish": item.translation,
                "Score": f"{item.overall_score:.1f}",
                "Breakdown (Context/Ling/UI/Cons)": breakdown_str,
                "Status": item.status,
                "Issues Found": issues_str,
                "Severity": item.severity,
                "Suggested Translation": item.suggested_translation,
                "Explanation": item.explanation,
            }
        )

    return pd.DataFrame(records)


def export_dataframe_to_csv(df: pd.DataFrame, prefix: str = "voxiis_export") -> str:
    """Export a Pandas DataFrame to a temporary CSV file and return its file path.

    Args:
        df: Pandas DataFrame to export.
        prefix: Filename prefix.

    Returns:
        Absolute filepath to the generated CSV file.
    """
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", prefix=f"{prefix}_", encoding="utf-8"
    )
    df.to_csv(temp_file.name, index=False, encoding="utf-8")
    temp_file.close()
    return temp_file.name


def export_models_to_json(models: Sequence[BaseModel], prefix: str = "voxiis_export") -> str:
    """Export a sequence of Pydantic models to a formatted JSON temporary file.

    Args:
        models: Sequence of Pydantic models.
        prefix: Filename prefix.

    Returns:
        Absolute filepath to the generated JSON file.
    """
    dict_list = [m.model_dump() for m in models]
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json", prefix=f"{prefix}_", encoding="utf-8"
    )
    json.dump(dict_list, temp_file, indent=2, ensure_ascii=False)
    temp_file.close()
    return temp_file.name
