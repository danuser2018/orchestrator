import re
import unicodedata
from typing import Tuple, List, Optional
from plugins.base import Plugin
from .models import UserRequest, PluginContext
from .plugin_manager import PluginManager
from .similarity import SimilarityEngine
from .logger import logger
from .config import settings

class PluginMatcher:
    def __init__(
        self, 
        plugin_manager: PluginManager, 
        similarity_engine: SimilarityEngine,
        similarity_threshold: float = settings.similarity_threshold,
        tie_breaker_threshold: float = settings.tie_breaker_threshold
    ):
        self.plugin_manager = plugin_manager
        self.similarity_engine = similarity_engine
        self.similarity_threshold = similarity_threshold
        self.tie_breaker_threshold = tie_breaker_threshold

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', ' ', text)
        return ' '.join(text.split())

    async def route_request(self, request: UserRequest) -> Tuple[Plugin | None, PluginContext]:
        normalized_text = self.normalize_text(request.text)
        context = PluginContext(raw_text=request.text, normalized_text=normalized_text)
        
        # Guard short-circuit if user text is empty
        if not normalized_text:
            logger.info("Empty user query. Defaulting to FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context
            
        plugins = self.plugin_manager.get_active_plugins()
        candidate_scores = []

        for plugin in plugins:
            if plugin.id == "fallback":
                continue
                
            best_phrase_score = 0.0
            best_phrase = ""
            
            for example in plugin.examples:
                normalized_example = self.normalize_text(example)
                phrase_score = self.similarity_engine.score(normalized_text, normalized_example)
                if phrase_score > best_phrase_score:
                    best_phrase_score = phrase_score
                    best_phrase = example
            
            candidate_scores.append({
                "plugin": plugin,
                "score": best_phrase_score,
                "priority": plugin.priority,
                "best_phrase": best_phrase
            })

        # Sort candidate plugins by score desc
        candidate_scores.sort(key=lambda x: x["score"], reverse=True)

        # Diagnose logging
        logger.debug(f"Input request: '{request.text}' | Normalized: '{normalized_text}'")
        logger.debug("Plugin candidates ranking:")
        for idx, entry in enumerate(candidate_scores):
            p = entry["plugin"]
            logger.debug(f"  [{idx + 1}] Plugin: {p.name} (id: {p.id}) | Score: {entry['score']:.2f} | Priority: {entry['priority']} | Winning Phrase: '{entry['best_phrase']}'")

        if not candidate_scores:
            logger.info("No active plugins found. Using FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context

        first = candidate_scores[0]
        
        # Check minimum similarity threshold
        if first["score"] < self.similarity_threshold:
            logger.info(f"Top candidate {first['plugin'].name} score {first['score']:.2f} below threshold {self.similarity_threshold}. Using FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context

        # Check for ties/ambiguities with the runner-up
        if len(candidate_scores) > 1:
            second = candidate_scores[1]
            score_difference = first["score"] - second["score"]
            
            if score_difference < self.tie_breaker_threshold:
                logger.info(
                    f"Ambiguity detected between {first['plugin'].name} (score: {first['score']:.2f}) "
                    f"and {second['plugin'].name} (score: {second['score']:.2f}). Difference: {score_difference:.2f} < tie_breaker_threshold: {self.tie_breaker_threshold}"
                )
                
                if first["priority"] > second["priority"]:
                    logger.info(f"Resolved tie in favor of {first['plugin'].name} by higher priority ({first['priority']} > {second['priority']})")
                    return first["plugin"], context
                elif second["priority"] > first["priority"]:
                    logger.info(f"Resolved tie in favor of {second['plugin'].name} by higher priority ({second['priority']} > {first['priority']})")
                    return second["plugin"], context
                else:
                    logger.warning(
                        f"Persistent tie between {first['plugin'].name} and {second['plugin'].name}. Both have priority {first['priority']}. Defaulting to FallbackPlugin."
                    )
                    fallback = self.plugin_manager.get_plugin("FallbackPlugin")
                    return fallback, context

        logger.info(f"Selected plugin: {first['plugin'].name} with score: {first['score']:.2f} and winning phrase: '{first['best_phrase']}'")
        return first["plugin"], context

class Router(PluginMatcher):
    # Kept for backward compatibility with external code using Router class name.
    pass

