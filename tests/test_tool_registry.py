import pytest
import os
from src.core.tools.tool_registry import ToolRegistry
from src.core.tools.tool_base import BaseTool
from src.core.tools.tool_loader import load_tools_from_directory

class DummyTestTool(BaseTool):
    @property
    def name(self): return "dummy"
    @property
    def description(self): return "doc"
    @property
    def parameters_schema(self): return {}
    async def execute(self, **kwargs): return "ok"

def test_tool_registry():
    """Test basic registry functions."""
    registry = ToolRegistry()
    registry._tools.clear() # reset singleton
    
    tool = DummyTestTool()
    registry.register(tool)
    
    assert registry.get_tool("dummy") is tool
    assert len(registry.get_all_tools()) == 1
    
    defs = registry.get_all_definitions()
    assert len(defs) == 1
    assert defs[0]["name"] == "dummy"

def test_tool_loader():
    """Test dynamic tool loader."""
    registry = ToolRegistry()
    registry._tools.clear()
    
    # Load from the actual src dir
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'core', 'tools')
    load_tools_from_directory(tools_dir)
    
    # Calendar, Docs, Drive, Memory tools should be loaded
    assert len(registry.get_all_tools()) > 0
    assert registry.get_tool("create_document") is not None
    assert registry.get_tool("remember") is not None
