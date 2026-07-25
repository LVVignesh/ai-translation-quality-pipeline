"""Gradio application interface for Voxiis AI Translation & Quality Scoring Pipeline.

Orchestrates UI interactions, handles state transitions, and invokes translation/scoring services.
Contains NO business logic, adhering to clean architecture principles.
"""

from typing import Optional, Tuple
import gradio as gr
import pandas as pd

from config import config
from logger import logger
from sample_data import SAMPLE_QUALITY_INPUTS, SAMPLE_TRANSLATION_INPUTS
from schemas import QualityEvaluationOutput, TranslationOutput
from scorer import QualityScorerService
from translator import TranslationService
from utils import (
    export_dataframe_to_csv,
    export_models_to_json,
    quality_outputs_to_dataframe,
    translation_outputs_to_dataframe,
)

# Global service instances
translator_service = TranslationService()
scorer_service = QualityScorerService()

# Global state caches for exports
cached_translation_results: list[TranslationOutput] = []
cached_quality_results: list[QualityEvaluationOutput] = []
cached_translation_df: pd.DataFrame = pd.DataFrame()
cached_quality_df: pd.DataFrame = pd.DataFrame()


def get_effective_api_key(user_api_key: Optional[str]) -> Optional[str]:
    """Helper to resolve user-entered API key vs environment configuration."""
    if user_api_key and user_api_key.strip():
        return user_api_key.strip()
    return config.anthropic_api_key if config.is_api_key_configured else None


def handle_translation_pipeline(
    user_api_key: Optional[str], progress=gr.Progress(track_tqdm=True)
) -> Tuple[pd.DataFrame, str]:
    """Orchestrate context-aware translation pipeline.

    Args:
        user_api_key: Optional API key input from UI.

    Returns:
        Tuple of (formatted DataFrame, status message).
    """
    global cached_translation_results, cached_translation_df
    effective_key = get_effective_api_key(user_api_key)

    if not effective_key:
        return (
            pd.DataFrame(),
            "⚠️ Error: Anthropic API key is not configured. Please enter your API key in the field above or set ANTHROPIC_API_KEY in your .env file.",
        )

    try:
        progress(0.1, desc="Initializing Translation Service...")
        results = translator_service.translate_batch(
            SAMPLE_TRANSLATION_INPUTS, api_key=effective_key
        )
        cached_translation_results = results
        cached_translation_df = translation_outputs_to_dataframe(results)

        progress(1.0, desc="Translation Complete!")
        status_msg = f"✅ Successfully translated {len(results)} context-aware UI strings using {config.model_name}."
        return cached_translation_df, status_msg

    except Exception as exc:
        logger.error(f"Translation pipeline error: {exc}")
        return pd.DataFrame(), f"❌ Translation Error: {str(exc)}"


def handle_scoring_pipeline(
    user_api_key: Optional[str], progress=gr.Progress(track_tqdm=True)
) -> Tuple[pd.DataFrame, str, str, str, str, str]:
    """Orchestrate quality scoring pipeline.

    Args:
        user_api_key: Optional API key input from UI.

    Returns:
        Tuple of (DataFrame, status_msg, passed_card, needs_review_card, avg_score_card, pass_rate_card).
    """
    global cached_quality_results, cached_quality_df
    effective_key = get_effective_api_key(user_api_key)

    if not effective_key:
        return (
            pd.DataFrame(),
            "⚠️ Error: Anthropic API key is not configured. Please enter your API key in the field above or set ANTHROPIC_API_KEY in your .env file.",
            "0",
            "0",
            "0.0",
            "0.0%",
        )

    try:
        progress(0.1, desc="Initializing Quality Auditor...")
        evaluations, summary = scorer_service.evaluate_batch(
            SAMPLE_QUALITY_INPUTS, api_key=effective_key
        )
        cached_quality_results = evaluations
        cached_quality_df = quality_outputs_to_dataframe(evaluations)

        progress(1.0, desc="Evaluation Complete!")
        status_msg = f"✅ Evaluated {summary.total_translated} candidate translations against 100-point rubric."

        passed_str = str(summary.passed_count)
        review_str = str(summary.needs_review_count)
        avg_str = f"{summary.average_score:.1f}"
        rate_str = f"{summary.pass_rate_percentage:.1f}%"

        return (
            cached_quality_df,
            status_msg,
            passed_str,
            review_str,
            avg_str,
            rate_str,
        )

    except Exception as exc:
        logger.error(f"Quality scoring pipeline error: {exc}")
        return pd.DataFrame(), f"❌ Quality Scoring Error: {str(exc)}", "0", "0", "0.0", "0.0%"


def handle_full_pipeline(
    user_api_key: Optional[str], progress=gr.Progress(track_tqdm=True)
) -> Tuple[pd.DataFrame, pd.DataFrame, str, str, str, str, str]:
    """Execute both translation and quality scoring pipelines sequentially.

    Args:
        user_api_key: Optional API key input from UI.

    Returns:
        Tuple updating Translation Table, Quality Table, Global Status, and KPI cards.
    """
    effective_key = get_effective_api_key(user_api_key)
    if not effective_key:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            "⚠️ Error: Anthropic API key is missing. Please provide a key above.",
            "0",
            "0",
            "0.0",
            "0.0%",
        )

    progress(0.1, desc="Starting Full Pipeline Execution...")
    trans_df, trans_msg = handle_translation_pipeline(effective_key, progress)

    if "Error" in trans_msg:
        return trans_df, pd.DataFrame(), trans_msg, "0", "0", "0.0", "0.0%"

    progress(0.5, desc="Starting Quality Scoring Phase...")
    score_df, score_msg, passed, review, avg, rate = handle_scoring_pipeline(
        effective_key, progress
    )

    full_msg = f"🚀 Full Pipeline Executed Successfully! | Translation Phase: Completed | Quality Phase: Completed (Pass Rate: {rate})"
    return trans_df, score_df, full_msg, passed, review, avg, rate


def export_translation_csv() -> Optional[str]:
    """Generate CSV file download for translation table."""
    if cached_translation_df.empty:
        return None
    return export_dataframe_to_csv(cached_translation_df, prefix="voxiis_translations")


def export_translation_json() -> Optional[str]:
    """Generate JSON file download for translation results."""
    if not cached_translation_results:
        return None
    return export_models_to_json(cached_translation_results, prefix="voxiis_translations")


def export_quality_csv() -> Optional[str]:
    """Generate CSV file download for quality scoring table."""
    if cached_quality_df.empty:
        return None
    return export_dataframe_to_csv(cached_quality_df, prefix="voxiis_quality_evaluations")


def export_quality_json() -> Optional[str]:
    """Generate JSON file download for quality scoring results."""
    if not cached_quality_results:
        return None
    return export_models_to_json(cached_quality_results, prefix="voxiis_quality_evaluations")


def create_app() -> gr.Blocks:
    """Build and configure the Gradio application layout."""
    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, title="Voxiis – AI Localization & Quality Scoring") as app:

        gr.Markdown(
            """
            # Voxiis – AI-Assisted Translation & Quality Scoring Pipeline
            **Production AI Engineering Assessment Application**
            
            This application demonstrates context-aware software localization and objective, explainable 100-point translation quality scoring powered by Claude.
            """
        )

        with gr.Row():
            user_api_key = gr.Textbox(
                label="Anthropic API Key (Optional override if not set in .env)",
                placeholder="sk-ant-...",
                type="password",
                scale=3,
            )
            run_full_btn = gr.Button("🚀 Run Full Pipeline", variant="primary", scale=1)

        global_status = gr.Markdown("Ready to process UI strings and evaluate translations.")

        with gr.Tabs():
            # TAB 1: TRANSLATION
            with gr.TabItem("Translation"):
                gr.Markdown("### Part 1: Context-Aware Software Localization")
                run_trans_btn = gr.Button("Translate Strings", variant="secondary")

                trans_table = gr.Dataframe(
                    headers=["Key", "English Text", "Spanish Translation", "Confidence", "Reasoning"],
                    datatype=["str", "str", "str", "str", "str"],
                    wrap=True,
                    interactive=False,
                )

                with gr.Row():
                    btn_trans_csv = gr.Button("📥 Export Translation CSV")
                    btn_trans_json = gr.Button("📥 Export Translation JSON")
                    file_trans_download = gr.File(label="Download File", interactive=False)

            # TAB 2: QUALITY SCORING
            with gr.TabItem("Quality Scoring"):
                gr.Markdown("### Part 2: Translation Quality Scoring Audit (100-Point Rubric)")
                run_score_btn = gr.Button("Evaluate Quality", variant="secondary")

                score_table = gr.Dataframe(
                    headers=[
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
                    ],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str", "str", "str"],
                    wrap=True,
                    interactive=False,
                )

                with gr.Row():
                    btn_score_csv = gr.Button("📥 Export Evaluation CSV")
                    btn_score_json = gr.Button("📥 Export Evaluation JSON")
                    file_score_download = gr.File(label="Download File", interactive=False)

        gr.Markdown("---")
        gr.Markdown("### 📊 Pipeline Executive Summary")
        with gr.Row():
            card_passed = gr.Textbox(label="Passed (Score ≥ 70)", value="0", interactive=False)
            card_review = gr.Textbox(label="Needs Review (Score < 70)", value="0", interactive=False)
            card_avg = gr.Textbox(label="Average Score", value="0.0", interactive=False)
            card_rate = gr.Textbox(label="Pass Rate", value="0.0%", interactive=False)

        # EVENT BINDINGS
        run_full_btn.click(
            fn=handle_full_pipeline,
            inputs=[user_api_key],
            outputs=[
                trans_table,
                score_table,
                global_status,
                card_passed,
                card_review,
                card_avg,
                card_rate,
            ],
        )

        run_trans_btn.click(
            fn=handle_translation_pipeline,
            inputs=[user_api_key],
            outputs=[trans_table, global_status],
        )

        run_score_btn.click(
            fn=handle_scoring_pipeline,
            inputs=[user_api_key],
            outputs=[
                score_table,
                global_status,
                card_passed,
                card_review,
                card_avg,
                card_rate,
            ],
        )

        btn_trans_csv.click(fn=export_translation_csv, outputs=[file_trans_download])
        btn_trans_json.click(fn=export_translation_json, outputs=[file_trans_download])
        btn_score_csv.click(fn=export_quality_csv, outputs=[file_score_download])
        btn_score_json.click(fn=export_quality_json, outputs=[file_score_download])

    return app


# Application entrypoint
app = create_app()

if __name__ == "__main__":
    app.launch()
