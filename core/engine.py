import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from plugins.base import Plugin
from nova_event_bus import EventBusInterface
from .models import UserRequest, PluginContext, ExecutionPlanStep, ExecutionPlan, AssistantResponse
from .plugin_manager import PluginManager
from .similarity import SimilarityEngine
from .logger import logger
from .config import settings
from .events import ResponseGeneratedEvent

class PluginNotFoundError(Exception):
    pass

class ExecutionPlanner:
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

    async def resolve(self, request: UserRequest) -> ExecutionPlan:
        correlation_id = request.correlation_id or str(uuid.uuid4())
        channel = request.channel or "voice"
        
        normalized_text = self.normalize_text(request.text)
        context = PluginContext(
            raw_text=request.text,
            normalized_text=normalized_text,
            correlation_id=correlation_id,
            channel=channel
        )
        
        # Guard short-circuit if user text is empty
        if not normalized_text:
            logger.info("Empty user query. Defaulting to fallback plugin.")
            step = ExecutionPlanStep(
                plugin="fallback",
                confidence=0.0,
                parameters={},
                channel=channel,
                context=context,
                security={}
            )
            return ExecutionPlan(steps=[step])
            
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
            logger.info("No active plugins found. Using fallback plugin.")
            step = ExecutionPlanStep(
                plugin="fallback",
                confidence=0.0,
                parameters={},
                channel=channel,
                context=context,
                security={}
            )
            return ExecutionPlan(steps=[step])

        first = candidate_scores[0]
        
        # Check minimum similarity threshold
        if first["score"] < self.similarity_threshold:
            logger.info(f"Top candidate {first['plugin'].name} score {first['score']:.2f} below threshold {self.similarity_threshold}. Using fallback plugin.")
            step = ExecutionPlanStep(
                plugin="fallback",
                confidence=first["score"],
                parameters={},
                channel=channel,
                context=context,
                security={}
            )
            return ExecutionPlan(steps=[step])

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
                    selected_plugin = first["plugin"]
                    confidence = first["score"]
                elif second["priority"] > first["priority"]:
                    logger.info(f"Resolved tie in favor of {second['plugin'].name} by higher priority ({second['priority']} > {first['priority']})")
                    selected_plugin = second["plugin"]
                    confidence = second["score"]
                else:
                    logger.warning(
                        f"Persistent tie between {first['plugin'].name} and {second['plugin'].name}. Both have priority {first['priority']}. Defaulting to fallback plugin."
                    )
                    selected_plugin = self.plugin_manager.get_plugin("fallback")
                    confidence = 0.0
                
                step = ExecutionPlanStep(
                    plugin=selected_plugin.id if selected_plugin else "fallback",
                    confidence=confidence,
                    parameters={},
                    channel=channel,
                    context=context,
                    security={}
                )
                return ExecutionPlan(steps=[step])

        logger.info(f"Selected plugin: {first['plugin'].name} (id: {first['plugin'].id}) with score: {first['score']:.2f} and winning phrase: '{first['best_phrase']}'")
        step = ExecutionPlanStep(
            plugin=first["plugin"].id,
            confidence=first["score"],
            parameters={},
            channel=channel,
            context=context,
            security={}
        )
        return ExecutionPlan(steps=[step])


class PlanExecutor:
    def __init__(self, plugin_manager: PluginManager, event_bus: Optional[EventBusInterface] = None):
        self.plugin_manager = plugin_manager
        self.event_bus = event_bus

    async def execute_plan(self, plan: ExecutionPlan) -> AssistantResponse:
        import time
        start_time = time.time()
        
        last_plugin_name = "None"
        last_speech = ""
        success = True
        
        for step in plan.steps:
            plugin = self.plugin_manager.get_plugin(step.plugin)
            if not plugin:
                logger.error(f"Plugin {step.plugin} not found in execution plan.")
                raise PluginNotFoundError(f"El plugin '{step.plugin}' no está registrado en el sistema.")
            
            last_plugin_name = plugin.name
            try:
                result = await plugin.execute(step.context)
                last_speech = result.speech
                if not result.success:
                    logger.warning(f"Plugin {plugin.name} execution failed.")
                    success = False
                    break
            except Exception as e:
                logger.error(f"Exception during execution of plugin {plugin.name}: {e}", exc_info=True)
                success = False
                last_speech = "Ha ocurrido un error interno al ejecutar la acción."
                break
                
        execution_time = int((time.time() - start_time) * 1000)
        response = AssistantResponse(
            success=success,
            plugin_used=last_plugin_name,
            speech=last_speech,
            execution_time_ms=execution_time
        )
        
        # Publish event if execution succeeded and event bus is available
        if success and self.event_bus:
            try:
                correlation_id = None
                channel = "voice"
                confidence = 0.0
                metadata = {}
                
                if plan.steps:
                    last_step = plan.steps[-1]
                    correlation_id = last_step.context.correlation_id
                    channel = last_step.channel or last_step.context.channel or "voice"
                    confidence = last_step.confidence or 0.0
                    metadata = last_step.context.metadata
                
                if not correlation_id:
                    correlation_id = str(uuid.uuid4())
                
                event = ResponseGeneratedEvent(
                    response=response.speech,
                    plugin=response.plugin_used,
                    confidence=confidence,
                    timestamp=datetime.now(timezone.utc),
                    correlation_id=correlation_id,
                    execution_time_ms=response.execution_time_ms,
                    channel=channel,
                    metadata=metadata
                )
                await self.event_bus.publish(event)
                logger.info(f"Published ResponseGeneratedEvent (correlation_id={correlation_id})")
            except Exception as exc:
                logger.error(f"Failed to publish ResponseGeneratedEvent: {exc}", exc_info=True)
                
        return response



