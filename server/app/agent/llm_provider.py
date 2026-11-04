"""LLM provider abstraction and implementations for Module B5."""

import json
import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.agent.schemas import RequestUnderstanding, ResearchPlan

logger = logging.getLogger("carti.agent.llm")

T = TypeVar("T", bound=BaseModel)


class ILLMProvider(Protocol):
    """Protocol for LLM provider operations."""

    async def generate_structured(
        self,
        prompt: str,
        schema_cls: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Generate validated structured output adhering to a Pydantic schema."""
        ...

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate free-form text response."""
        ...


class GeminiLLMProvider:
    """Google Gemini LLM provider using direct REST API via HTTPX."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_structured(
        self,
        prompt: str,
        schema_cls: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Call Gemini with JSON mode and validate against schema."""
        if not self.api_key:
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message="Gemini API key is not configured.",
                retryable=False,
            )

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "responseMimeType": "application/json",
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException:
            logger.error("Gemini API call timed out after %ss", self.timeout_seconds)
            raise CartiAPIException(
                code=CartiErrorCode.AGENT_TIMEOUT,
                message="LLM provider request timed out.",
                retryable=True,
            )
        except httpx.RequestError as exc:
            logger.error("Gemini network error: %s", exc)
            raise CartiAPIException(
                code=CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE,
                message="LLM provider network error.",
                retryable=True,
            )

        if response.status_code == 429:
            raise CartiAPIException(
                code=CartiErrorCode.RATE_LIMIT_EXCEEDED,
                message="LLM provider rate limit exceeded.",
                retryable=True,
            )
        elif response.status_code >= 500:
            raise CartiAPIException(
                code=CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE,
                message=f"LLM provider unavailable (HTTP {response.status_code}).",
                retryable=True,
            )
        elif response.status_code != 200:
            logger.error("Gemini error status %s: %s", response.status_code, response.text)
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message=f"LLM provider error (HTTP {response.status_code}).",
                retryable=False,
            )

        try:
            resp_data = response.json()
            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned by Gemini.")
            text_content = candidates[0]["content"]["parts"][0]["text"]
            return schema_cls.model_validate_json(text_content)
        except (KeyError, IndexError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            logger.error("Failed to parse Gemini structured response: %s", exc)
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message="LLM generated invalid structured output.",
                retryable=False,
                details={"error": str(exc)},
            )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Call Gemini for plain text generation."""
        if not self.api_key:
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message="Gemini API key is not configured.",
                retryable=False,
            )

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException:
            raise CartiAPIException(
                code=CartiErrorCode.AGENT_TIMEOUT,
                message="LLM provider request timed out.",
                retryable=True,
            )
        except httpx.RequestError as exc:
            raise CartiAPIException(
                code=CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE,
                message="LLM provider network error.",
                retryable=True,
            )

        if response.status_code != 200:
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message=f"LLM provider error (HTTP {response.status_code}).",
                retryable=False,
            )

        resp_data = response.json()
        candidates = resp_data.get("candidates", [])
        if not candidates:
            return ""
        return candidates[0]["content"]["parts"][0]["text"]


class MockLLMProvider:
    """Configurable mock and rule-based LLM provider for reliable, deterministic tests."""

    def __init__(self):
        self.preset_responses: List[Any] = []
        self.should_timeout = False
        self.should_fail_rate_limit = False
        self.should_fail_invalid_json = False
        self.should_fail_provider_unavailable = False
        self.call_history: List[Dict[str, Any]] = []

    def queue_response(self, response: Any) -> None:
        """Queue a specific response to return on the next call."""
        self.preset_responses.append(response)

    async def generate_structured(
        self,
        prompt: str,
        schema_cls: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Generate structured response, checking mock triggers or using rule-based synthesis."""
        self.call_history.append({
            "prompt": prompt,
            "schema": schema_cls.__name__,
            "system_instruction": system_instruction,
        })

        if self.should_timeout:
            raise CartiAPIException(
                code=CartiErrorCode.AGENT_TIMEOUT,
                message="Mock LLM provider simulated timeout.",
                retryable=True,
            )

        if self.should_fail_rate_limit:
            raise CartiAPIException(
                code=CartiErrorCode.RATE_LIMIT_EXCEEDED,
                message="Mock LLM provider simulated rate limit.",
                retryable=True,
            )

        if self.should_fail_provider_unavailable:
            raise CartiAPIException(
                code=CartiErrorCode.DOWNSTREAM_SERVICE_UNAVAILABLE,
                message="Mock LLM provider simulated service unavailable.",
                retryable=True,
            )

        if self.should_fail_invalid_json:
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message="LLM generated invalid structured output.",
                retryable=False,
                details={"error": "Malformed JSON: Expecting value: line 1 column 1 (char 0)"},
            )

        if self.preset_responses:
            item = self.preset_responses.pop(0)
            if isinstance(item, Exception):
                raise item
            if isinstance(item, schema_cls):
                return item
            if isinstance(item, dict):
                return schema_cls.model_validate(item)
            if isinstance(item, str):
                return schema_cls.model_validate_json(item)

        # Rule-based fallback synthesis
        return self._synthesize_rule_based(prompt, schema_cls)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate text response."""
        self.call_history.append({
            "prompt": prompt,
            "system_instruction": system_instruction,
        })

        if self.should_timeout:
            raise CartiAPIException(
                code=CartiErrorCode.AGENT_TIMEOUT,
                message="Mock LLM provider simulated timeout.",
                retryable=True,
            )

        if self.preset_responses:
            item = self.preset_responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return str(item)

        return "Synthesized recommendation: The product meets all stated requirements and price caps."

    def _synthesize_rule_based(self, prompt: str, schema_cls: Type[T]) -> T:
        """Generate a realistic, deterministic response from prompt text."""
        user_text = prompt
        if "<<<UNTRUSTED_USER_REQUEST_START>>>" in prompt:
            parts = prompt.split("<<<UNTRUSTED_USER_REQUEST_START>>>")[1].split("<<<UNTRUSTED_USER_REQUEST_END>>>")
            user_text = parts[0].strip()

        lower = user_text.lower()

        if schema_cls == RequestUnderstanding:
            # Check for ambiguity
            if any(term in lower for term in ["something nice", "whatever", "surprise me", "anything"]):
                return RequestUnderstanding(
                    original_request=user_text,
                    product_type="unknown",
                    is_clarification_needed=True,
                    clarification_reason="Request is too ambiguous to identify a specific product category.",
                    confidence_score=0.2,
                )

            # Check for conflicting requirements
            if "free" in lower and "under $0" in lower:
                return RequestUnderstanding(
                    original_request=user_text,
                    product_type="unknown",
                    is_clarification_needed=True,
                    clarification_reason="Conflicting or impossible price constraints specified.",
                    confidence_score=0.1,
                )

            # Extract category
            category = "General"
            if any(k in lower for k in ["lamp", "desk lamp", "chair", "sofa", "furniture", "light", "pillow"]):
                category = "Home"
            elif any(k in lower for k in ["laptop", "mouse", "keyboard", "monitor", "headphones", "phone"]):
                category = "Electronics"
            elif any(k in lower for k in ["shirt", "shoes", "jacket", "hoodie", "pants"]):
                category = "Clothing"

            # Extract brand
            brand = None
            for b in ["apple", "logitech", "anker", "ikea", "sony", "samsung", "lumino", "aura"]:
                if b in lower:
                    brand = b.capitalize()
                    break

            # Extract price
            price_pref = None
            price_match = re.search(r"\$(\d+(?:\.\d{2})?)", user_text) or re.search(r"under\s+\$?(\d+(?:\.\d{2})?)", lower)
            if price_match:
                try:
                    price_pref = Decimal(price_match.group(1))
                except Exception:
                    pass

            # Extract explicit requirements
            explicit = []
            if "warm" in lower or "warm-light" in lower:
                explicit.append("warm light")
            if "ergonomic" in lower:
                explicit.append("ergonomic design")
            if "wireless" in lower:
                explicit.append("wireless connectivity")
            if "quiet" in lower:
                explicit.append("quiet operation")

            # Extract exclusions
            exclusions = []
            if "no plastic" in lower:
                exclusions.append("plastic")
            if "without wire" in lower or "no wires" in lower:
                exclusions.append("wired")

            # Extract quantity
            quantity = 1
            qty_match = re.search(r"\b(?:buy|order|get|need)\s+(\d+)\b", lower) or re.search(r"\b(\d+)\s+(?:units|items|pieces|lamps|desk lamps|mice|keyboards)\b", lower)
            if qty_match:
                try:
                    quantity = min(50, max(1, int(qty_match.group(1))))
                except Exception:
                    pass

            return RequestUnderstanding(
                original_request=user_text,
                product_type="desk lamp" if "lamp" in lower else ("keyboard" if "keyboard" in lower else "item"),
                category=category,
                brand_preference=brand,
                explicit_requirements=explicit,
                inferred_preferences=["reliable quality", "good reviews"],
                exclusions=exclusions,
                price_preference=price_pref,
                quantity=quantity,
                retailer_preferences=["target.com", "amazon.com"],
                is_clarification_needed=False,
                confidence_score=0.95,
            )

        elif schema_cls == ResearchPlan:
            return ResearchPlan(
                research_objective="Discover best matching products under user mandate",
                search_queries=["desk lamp warm light", "adjustable desk lamp"],
                constraints={"max_price": "40.00", "currency": "USD"},
                approved_tools=["search_products", "get_product", "propose_purchase"],
                max_steps=3,
            )

        # Default fallback: instantiate default schema
        try:
            return schema_cls()  # type: ignore
        except Exception:
            raise CartiAPIException(
                code=CartiErrorCode.LLM_PROVIDER_ERROR,
                message=f"Cannot synthesize default instance for {schema_cls.__name__}",
            )


def get_default_llm_provider() -> ILLMProvider:
    """Factory to retrieve configured LLM provider."""
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "mock" or not settings.LLM_API_KEY:
        return MockLLMProvider()
    return GeminiLLMProvider(
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
