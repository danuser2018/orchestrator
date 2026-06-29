import re
import unicodedata
from typing import Tuple

from .models import UserRequest, PluginContext
from .plugin_manager import PluginManager
from .logger import logger
from plugins.base import Plugin

class Router:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', ' ', text)
        return ' '.join(text.split())

    def calculate_score(self, plugin: Plugin, normalized_text: str) -> int:
        score = 0
        words = set(normalized_text.split())
        
        for keyword in plugin.keywords:
            if keyword.lower() in words:
                score += 1
                
        for pattern in plugin.regex_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                score += 5
                
        return score

    async def route_request(self, request: UserRequest) -> Tuple[Plugin | None, PluginContext]:
        normalized_text = self.normalize_text(request.text)
        context = PluginContext(raw_text=request.text, normalized_text=normalized_text)
        
        plugins = self.plugin_manager.get_active_plugins()
        
        # Check for exclusive regex matches first
        for plugin in plugins:
            if plugin.name == "FallbackPlugin":
                continue
            if plugin.exclusive_regex and re.search(plugin.exclusive_regex, normalized_text, re.IGNORECASE):
                logger.info(f"Selected plugin: {plugin.name} via exclusive regex match.")
                return plugin, context

        best_plugin = None
        highest_score = 0

        for plugin in plugins:
            if plugin.name == "FallbackPlugin":
                continue
            score = self.calculate_score(plugin, normalized_text)
            logger.debug(f"Plugin {plugin.name} score: {score}")
            if score > highest_score:
                highest_score = score
                best_plugin = plugin

        if highest_score > 0 and best_plugin:
            logger.info(f"Selected plugin: {best_plugin.name} with score: {highest_score}")
            return best_plugin, context
            
        logger.info("No plugin matched. Using FallbackPlugin.")
        fallback = self.plugin_manager.get_plugin("FallbackPlugin")
        return fallback, context
