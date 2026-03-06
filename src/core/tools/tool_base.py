from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """Abstract base class for all AI tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool, matching what the LLM will see. Example: 'search_news'"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A clear description of what the tool does and when the LLM should use it."""
        pass
        
    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """The JSON schema dict defining the parameters this tool accepts.
        
        Example:
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
        """
        pass
        
    def get_definition(self) -> dict[str, Any]:
        """Returns the full tool definition dictionary ready for the LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }
        
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """The actual execution logic of the tool.
        
        Args:
            **kwargs: Parameters passed by the LLM, matching parameters_schema
            
        Returns:
            The result of the tool execution, usually a string to be sent back to the LLM.
        """
        pass
