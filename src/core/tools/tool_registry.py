import logging
from typing import Any
from src.core.tools.tool_base import BaseTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Central registry holding all available tools."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tools: dict[str, BaseTool] = {}
        self._initialized = True
        logger.info("ToolRegistry initialized")

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        """Get all registered tool instances."""
        return list(self._tools.values())

    def get_all_definitions(self) -> list[dict[str, Any]]:
        """Get LLM-ready definitions for all tools."""
        return [tool.get_definition() for tool in self._tools.values()]

# Global singleton instance
registry = ToolRegistry()
