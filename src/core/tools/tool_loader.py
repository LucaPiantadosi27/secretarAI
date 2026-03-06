import importlib
import inspect
import logging
import os
import sys
from typing import Type

from src.core.tools.tool_base import BaseTool
from src.core.tools.tool_registry import registry

logger = logging.getLogger(__name__)

def load_tools_from_directory(directory_path: str) -> None:
    """Dynamically load and register all subclasses of BaseTool in a directory.
    
    Args:
        directory_path: Absolute or relative path to the tools directory
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        logger.warning(f"Tools directory not found: {directory_path}")
        return

    # To enable import logic, we might need the package name if not absolute.
    # A robust way is to append to sys.path temporarily or use importlib.util
    # Assuming tools are within the project's 'src' structure.
    
    loaded_count = 0
    for filename in os.listdir(directory_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            
            # Create absolute path and load module directly
            file_path = os.path.join(directory_path, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    
                    # Find and register tool classes
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseTool) and obj is not BaseTool:
                            # Instantiate and register
                            tool_instance = obj()
                            registry.register(tool_instance)
                            loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load tool module {filename}: {e}", exc_info=True)

    logger.info(f"Dynamically loaded {loaded_count} tools from {directory_path}")
