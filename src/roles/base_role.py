from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..web_search import SearchResult
from ..llm_handler import LLMResponse

@dataclass
class RoleResponse:
    """Base class for role responses that will be rendered in the UI"""
    role_name: str
    formatted_data: Dict[str, Any]
    search_results: List[SearchResult]
    llm_response: LLMResponse
    total_time: float

class BaseRole(ABC):
    """Base class for all AI agent roles in NeuralNexus"""
    
    def __init__(self):
        self.role_name = self.__class__.__name__
        self.system_prompt = self._get_system_prompt()
        self.web_search = None
        self.llm = None
    
    def initialize(self, web_search, llm):
        """Initialize role with required services"""
        self.web_search = web_search
        self.llm = llm
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt for this role"""
        pass
    
    @abstractmethod
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        pass
    
    @abstractmethod
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components specification for this role"""
        pass
    
    def get_search_context(self) -> str:
        """Return context for search enhancement"""
        return self.system_prompt
