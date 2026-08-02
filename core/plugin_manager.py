import importlib
import inspect
import sys
from pathlib import Path
from typing import List, Dict

from .logger import logger
from plugins.base import Plugin

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Plugin] = {}

    def discover_and_load(self):
        logger.info(f"Scanning for plugins in {self.plugins_dir}")
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist.")
            return

        parent_dir = str(self.plugins_dir.parent.absolute())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "main.py").exists() and item.name != "__pycache__":
                module_name = f"plugins.{item.name}.main"
                try:
                    module = importlib.import_module(module_name)
                    self._register_plugins_from_module(module)
                except Exception as e:
                    logger.error(f"Failed to load plugin module {module_name}: {e}", exc_info=True)

    def _register_plugins_from_module(self, module):
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj is not Plugin:
                if obj.__name__ not in self.plugins:
                    plugin_instance = obj()
                    
                    # Validate priority
                    if not (0 <= plugin_instance.priority <= 100):
                        raise ValueError(f"Plugin priority must be between 0 and 100, got {plugin_instance.priority}")
                        
                    # Validate unique ID
                    if any(p.id == plugin_instance.id for p in self.plugins.values()):
                        raise ValueError(f"Duplicate plugin ID: {plugin_instance.id}")
                        
                    try:
                        plugin_instance.initialize()
                        self.plugins[plugin_instance.id] = plugin_instance
                        self.plugins[plugin_instance.name] = plugin_instance
                        logger.info(f"Loaded plugin: {plugin_instance.name} (id: {plugin_instance.id})")
                    except Exception as e:
                        logger.error(f"Failed to initialize plugin {name}: {e}", exc_info=True)

    def get_active_plugins(self) -> List[Plugin]:
        unique_plugins = {}
        for plugin in self.plugins.values():
            unique_plugins[plugin.id] = plugin
        return list(unique_plugins.values())

    def get_plugin(self, identifier: str) -> Plugin | None:
        if identifier in self.plugins:
            return self.plugins[identifier]
        for plugin in self.plugins.values():
            if plugin.id.lower() == identifier.lower() or plugin.name.lower() == identifier.lower():
                return plugin
        return None



    def teardown(self):
        for name, plugin in self.plugins.items():
            try:
                plugin.teardown()
                logger.info(f"Teardown plugin: {name}")
            except Exception as e:
                logger.error(f"Error during teardown of plugin {name}: {e}", exc_info=True)
