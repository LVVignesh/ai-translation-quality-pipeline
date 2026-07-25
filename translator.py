"""Translation pipeline service for the AI Translation & Quality Scoring Pipeline.

Handles context-aware software localization by orchestrating prompt templates,
invoking the dedicated Claude client, and validating output with Pydantic schemas.
"""

from typing import List, Optional
from pydantic import ValidationError
from claude_client import ClaudeClient, ClaudeClientError
from logger import logger
from prompts import TRANSLATION_SYSTEM_PROMPT, TRANSLATION_USER_PROMPT_TEMPLATE
from schemas import TranslationInput, TranslationOutput


class TranslationService:
    """Service layer responsible for context-aware software string localization."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None) -> None:
        """Initialize the Translation service.

        Args:
            claude_client: Instance of ClaudeClient. If None, instantiates default.
        """
        self.client = claude_client or ClaudeClient()

    def translate_single(
        self, item: TranslationInput, api_key: Optional[str] = None
    ) -> TranslationOutput:
        """Translate a single UI string using its key and developer context.

        Args:
            item: TranslationInput containing key, context, and english text.
            api_key: Optional dynamic Anthropic API key.

        Returns:
            Validated TranslationOutput model.

        Raises:
            ClaudeClientError: If translation fails or API key is invalid.
        """
        user_prompt = TRANSLATION_USER_PROMPT_TEMPLATE.format(
            key=item.key, context=item.context, english=item.english
        )

        raw_dict = self.client.generate_json_completion(
            system_prompt=TRANSLATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            override_api_key=api_key,
            temperature=0.0,
        )

        # Validate with Pydantic schema
        try:
            return TranslationOutput(**raw_dict)
        except (ValidationError, Exception) as validation_err:
            logger.error(f"Pydantic schema validation error for key '{item.key}': {validation_err}")
            # Fallback construct if minor schema deviation occurs
            return TranslationOutput(
                key=item.key,
                english=item.english,
                translation=raw_dict.get("translation", item.english),
                confidence=raw_dict.get("confidence", "Medium"),
                reasoning=raw_dict.get("reasoning", "Translation extracted with fallback schema parsing."),
            )

    def translate_batch(
        self, items: List[TranslationInput], api_key: Optional[str] = None
    ) -> List[TranslationOutput]:
        """Translate a list of UI strings sequentially with progress logging.

        Args:
            items: List of TranslationInput instances.
            api_key: Optional dynamic Anthropic API key.

        Returns:
            List of validated TranslationOutput instances.
        """
        logger.info(f"Starting batch translation for {len(items)} UI strings...")
        results: List[TranslationOutput] = []

        for idx, item in enumerate(items, start=1):
            logger.info(f"Processing string {idx}/{len(items)}: key='{item.key}'")
            try:
                translated = self.translate_single(item, api_key=api_key)
                results.append(translated)
            except ClaudeClientError as err:
                logger.error(f"Failed to translate key '{item.key}': {err}")
                # Create an explicit error record rather than breaking the pipeline
                results.append(
                    TranslationOutput(
                        key=item.key,
                        english=item.english,
                        translation="[Translation Error]",
                        confidence="Low",
                        reasoning=f"API Error during translation: {str(err)}",
                    )
                )

        logger.info(f"Successfully completed batch translation for {len(results)} items.")
        return results
