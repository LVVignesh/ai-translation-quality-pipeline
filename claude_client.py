"""Dedicated Anthropic Claude API client wrapper for Voxiis.

Centralizes all Claude API invocations, environment/model resolution, retry logic with
exponential backoff, robust JSON extraction/parsing, timeout handling, and exception management.
"""

import json
import re
import time
from typing import Any, Dict, Optional
import anthropic
from config import config
from logger import logger


class ClaudeClientError(Exception):
    """Custom exception raised for Claude client errors."""

    pass


class ClaudeClient:
    """Wrapper class encapsulating all interaction with the Anthropic Claude API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Initialize the Claude API client.

        Args:
            api_key: Optional override for Anthropic API key. Defaults to config setting.
            model_name: Optional override for model name. Defaults to config setting.
            max_retries: Optional override for max retry attempts. Defaults to config setting.
            timeout: Optional override for request timeout in seconds. Defaults to config setting.
        """
        self.api_key = api_key or config.anthropic_api_key
        self.model_name = model_name or config.model_name
        self.max_retries = max_retries if max_retries is not None else config.max_retries
        self.timeout = timeout if timeout is not None else config.request_timeout

    def _get_client(self, override_api_key: Optional[str] = None) -> anthropic.Anthropic:
        """Instantiate an Anthropic client, checking for API key validity.

        Args:
            override_api_key: Optional key passed dynamically at request time.

        Returns:
            Initialized anthropic.Anthropic instance.

        Raises:
            ClaudeClientError: If no valid API key is available.
        """
        effective_key = override_api_key or self.api_key
        if not effective_key or not effective_key.strip():
            logger.error("Anthropic API key is missing.")
            raise ClaudeClientError(
                "Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in your .env file "
                "or provide a valid API key in the application interface."
            )
        return anthropic.Anthropic(api_key=effective_key.strip(), timeout=self.timeout)

    def extract_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Robustly parse raw string or markdown-wrapped JSON responses from LLM.

        Parsing Flow:
        1. Attempt direct JSON string parse.
        2. Attempt extraction from markdown code block (` ```json { ... } ``` `).
        3. Fallback to safest non-greedy pattern matching first JSON object.

        Args:
            raw_text: Content returned by Claude API.

        Returns:
            Parsed dictionary.

        Raises:
            ClaudeClientError: If JSON cannot be extracted or decoded.
        """
        text = raw_text.strip()

        # Step 1: Direct JSON parse attempt
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Step 2: Extract JSON from markdown code blocks (```json ... ``` or ``` ... ```)
        json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Step 3: Non-greedy fallback regex to capture first standalone JSON object block
        json_object_match = re.search(r"(\{.*?\})", text, re.DOTALL)
        if json_object_match:
            try:
                return json.loads(json_object_match.group(1))
            except json.JSONDecodeError as err:
                logger.error(f"Failed to parse extracted JSON block: {err}")

        logger.error(f"Malformed LLM JSON response: {raw_text[:200]}...")
        raise ClaudeClientError(f"Unable to parse structured JSON from Claude response. Raw text: {raw_text[:150]}")

    def generate_json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        override_api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Execute a completion request to Claude, returning parsed JSON with retry handling.

        Retry Strategy:
        - Intercepts transient network errors (RateLimitError, APITimeoutError, APIConnectionError).
        - Executes exponential backoff retries up to max_retries limit.
        - Non-transient API errors fail immediately with clear diagnostic message.

        Args:
            system_prompt: Instructs model role and output requirements.
            user_prompt: Specific task input payload.
            override_api_key: Optional runtime API key.
            temperature: Sampling temperature (0.0 for deterministic JSON output).
            max_tokens: Maximum token limit for LLM response generation (default 1024).

        Returns:
            Parsed dictionary payload matching requested schema.

        Raises:
            ClaudeClientError: On non-transient API failure, missing key, or unparseable output.
        """
        client = self._get_client(override_api_key=override_api_key)
        attempt = 0
        backoff_seconds = 1.0

        while attempt <= self.max_retries:
            try:
                logger.info(
                    f"Calling Claude API (Model: {self.model_name}, Attempt: {attempt + 1}/{self.max_retries + 1})"
                )

                response = client.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                # Extract response text
                if not response.content:
                    raise ClaudeClientError("Received empty response content from Anthropic API.")

                raw_text = response.content[0].text
                parsed_data = self.extract_and_parse_json(raw_text)
                return parsed_data

            except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as transient_err:
                attempt += 1
                if attempt > self.max_retries:
                    logger.error(f"Max retry attempts reached for transient error: {transient_err}")
                    raise ClaudeClientError(f"Anthropic API transient error after retries: {str(transient_err)}")
                
                logger.warning(
                    f"Transient Claude API error: {transient_err}. Retrying in {backoff_seconds}s (Attempt {attempt})..."
                )
                time.sleep(backoff_seconds)
                backoff_seconds *= 2.0  # Exponential backoff

            except anthropic.APIError as api_err:
                logger.error(f"Anthropic API error: {api_err}")
                raise ClaudeClientError(f"Anthropic API error: {str(api_err)}")

            except Exception as exc:
                if isinstance(exc, ClaudeClientError):
                    raise exc
                logger.error(f"Unexpected error during Claude completion: {exc}")
                raise ClaudeClientError(f"Failed to process request: {str(exc)}")
