from typing import Dict, Any
import os
import logging
from datetime import datetime

from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """Model for LLM responses"""
    raw_response: str
    parsed_response: Dict[str, Any]
    processing_time: float

class LLMHandler:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url='https://glhf.chat/api/openai/v1',
            api_key=os.getenv('GLHF_API_KEY')
        )
        self.model = OpenAIModel(
            os.getenv('LLM_MODEL', 'hf:meta-llama/Llama-3.3-70B-Instruct'),
            openai_client=self.client
        )
    
    async def get_response(
        self, 
        system_prompt: str, 
        user_query: str, 
        search_results: list,
        role_parser: callable
    ) -> LLMResponse:
        """
        Get response from LLM with role-specific parsing.
        
        Args:
            system_prompt: Role-specific system prompt
            user_query: User's query
            search_results: List of search results
            role_parser: Role-specific function to parse LLM response
            
        Returns:
            LLMResponse object containing raw and parsed response
        """
        try:
            # Format search results for the prompt
            formatted_results = "\n".join([
                f"Source: {result.title}\nURL: {result.url}\n{result.description}\n"
                for result in search_results
            ])
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            messages = [
                {"role": "system", "content": f"{system_prompt}\nCurrent time: {current_time}"},
                {"role": "user", "content": f"Query: {user_query}\n\nSearch Results:\n{formatted_results}"}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            raw_response = response.choices[0].message.content
            parsed_response = role_parser(raw_response)
            
            return LLMResponse(
                raw_response=raw_response,
                parsed_response=parsed_response,
                processing_time=response.usage.total_tokens / 1000.0  # Approximate time based on tokens
            )
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            raise
