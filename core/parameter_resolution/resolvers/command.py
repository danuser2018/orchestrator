import re
import unicodedata
import logging
from typing import Optional, List, Tuple
from rapidfuzz import fuzz

from core.config import settings
from core.models import PluginContext
from core.parameter_resolution.base import BaseParameterResolver
from core.parameter_resolution.models import (
    ParameterDefinition,
    ParameterResolutionResult,
    ParameterResolutionStatus,
)
from core.command_catalog import CommandCatalogProjection

logger = logging.getLogger(__name__)


class CommandResolver(BaseParameterResolver):
    """
    Deterministic resolver that transforms natural language phrases into
    logical command identifiers based on the public command catalog projection.

    Design rationale for fuzz.ratio:
    Matching operates strictly on the full normalized phrase (Full Phrase Matching)
    and forbids semantic inference or arbitrary substring extraction. Metrics such as
    partial_ratio or token_sort_ratio would allow phrases containing isolated overlapping
    words to trigger commands accidentally. fuzz.ratio computes the global Levenshtein
    similarity of the entire phrase, strictly bounded to absorb minor STT transcription
    errors without risking critical false positives.
    """

    DEFAULT_RISK_THRESHOLDS = {
        "low": 60.0,
        "medium": 65.0,
        "high": 70.0,
    }
    DEFAULT_AMBIGUITY_DELTA = 5.0

    def __init__(
        self,
        catalog_projection: CommandCatalogProjection,
        thresholds: Optional[dict] = None,
        ambiguity_delta: Optional[float] = None,
    ):
        self.catalog = catalog_projection
        self.thresholds = thresholds or {
            "low": getattr(settings, "command_resolver_threshold_low", self.DEFAULT_RISK_THRESHOLDS["low"]),
            "medium": getattr(settings, "command_resolver_threshold_medium", self.DEFAULT_RISK_THRESHOLDS["medium"]),
            "high": getattr(settings, "command_resolver_threshold_high", self.DEFAULT_RISK_THRESHOLDS["high"]),
        }
        self.ambiguity_delta = (
            ambiguity_delta
            if ambiguity_delta is not None
            else getattr(settings, "command_resolver_ambiguity_delta", self.DEFAULT_AMBIGUITY_DELTA)
        )

    @property
    def target_type(self) -> str:
        return "Command"

    @staticmethod
    def normalize_phrase(text: Optional[str]) -> str:
        """
        Applies Unicode normalization (NFKD), strips accents, removes punctuation,
        converts to lowercase and collapses whitespace.
        """
        if not text:
            return ""
        # 1. Unicode normalization and strip diacritics
        decomposed = unicodedata.normalize("NFKD", text)
        without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
        # 2. Lowercase
        lowered = without_accents.lower()
        # 3. Remove punctuation (keep alphanumeric and whitespace)
        cleaned = re.sub(r"[^\w\s]", " ", lowered)
        # 4. Collapse whitespace
        normalized = " ".join(cleaned.split())
        return normalized

    async def resolve(
        self,
        context: PluginContext,
        definition: ParameterDefinition,
    ) -> ParameterResolutionResult:
        # Fail-closed if catalog is not available or empty
        if not self.catalog.is_ready:
            logger.warning("CommandResolver: Cannot resolve parameter; command catalog not received yet.")
            return ParameterResolutionResult(
                parameter_name=definition.name,
                value=None,
                status=(
                    ParameterResolutionStatus.UNRESOLVED_REQUIRED
                    if definition.required
                    else ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                ),
                error_message="Command catalog is empty or has not been received from host-service.",
            )

        input_text = (context.normalized_text if context.normalized_text is not None else context.raw_text) or ""
        normalized_input = self.normalize_phrase(input_text)

        if not normalized_input:
            return ParameterResolutionResult(
                parameter_name=definition.name,
                value=None,
                status=(
                    ParameterResolutionStatus.UNRESOLVED_REQUIRED
                    if definition.required
                    else ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                ),
                error_message="Empty input phrase after normalization.",
            )

        commands = self.catalog.list_commands()

        # Step 1: Exact Phrase Matching (Precedence over Fuzzy)
        for cmd in commands:
            for phrase in cmd.normalized_phrases:
                if normalized_input == phrase:
                    logger.info(
                        f"CommandResolver: Exact match found for '{normalized_input}' → '{cmd.name}'"
                    )
                    return ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=cmd.name,
                        status=ParameterResolutionStatus.RESOLVED,
                    )

        # Step 2: Fuzzy Matching with RapidFuzz
        candidates: List[Tuple[str, float, str]] = []  # (command_name, score, risk)
        for cmd in commands:
            threshold = self.thresholds.get(cmd.risk, self.thresholds["high"])
            best_score = 0.0
            for phrase in cmd.normalized_phrases:
                score = fuzz.ratio(normalized_input, phrase)
                if score > best_score:
                    best_score = score

            if best_score >= threshold:
                candidates.append((cmd.name, best_score, cmd.risk))

        if not candidates:
            logger.info(f"CommandResolver: No candidate matched threshold for input '{normalized_input}'")
            return ParameterResolutionResult(
                parameter_name=definition.name,
                value=None,
                status=(
                    ParameterResolutionStatus.UNRESOLVED_REQUIRED
                    if definition.required
                    else ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                ),
                error_message="No matching command found above risk threshold.",
            )

        # Sort descending by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        winner_name, winner_score, _ = candidates[0]

        # Step 3: Ambiguity Check
        if len(candidates) > 1:
            second_name, second_score, _ = candidates[1]
            if (winner_score - second_score) <= self.ambiguity_delta:
                logger.warning(
                    f"CommandResolver: Ambiguous resolution between '{winner_name}' ({winner_score:.1f}) "
                    f"and '{second_name}' ({second_score:.1f}). Discarding match."
                )
                return ParameterResolutionResult(
                    parameter_name=definition.name,
                    value=None,
                    status=(
                        ParameterResolutionStatus.UNRESOLVED_REQUIRED
                        if definition.required
                        else ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                    ),
                    error_message=f"Ambiguous match between {winner_name} and {second_name}.",
                )

        logger.info(
            f"CommandResolver: Fuzzy match accepted '{normalized_input}' → '{winner_name}' "
            f"(score={winner_score:.1f})"
        )
        return ParameterResolutionResult(
            parameter_name=definition.name,
            value=winner_name,
            status=ParameterResolutionStatus.RESOLVED,
        )
