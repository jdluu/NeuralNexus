import re
from typing import Any, Dict, List, Tuple
from .base_role import BaseRole

class creative_writer(BaseRole):
    """
    Creative Writer role that provides engaging, well-structured content.
    Focuses on storytelling, creative expression, and engaging writing.
    """
    
    def __init__(self):
        self.name = "Creative Writer"
        self.description = "Creates engaging, well-structured content with creative flair"
        self._system_prompt = """You are a Creative Writer AI assistant focused on:
1. Crafting engaging narratives
2. Developing creative content
3. Maintaining consistent style
4. Using vivid descriptions
5. Creating emotional resonance

When creating content:
- Use descriptive language
- Incorporate storytelling elements
- Maintain consistent tone and voice
- Consider the target audience
- Balance creativity with clarity

Always:
- Be original and creative
- Use varied vocabulary
- Create emotional connections
- Maintain narrative flow
- Consider pacing and structure"""
        super().__init__()

    def format_response(self, raw_response: str) -> str:
        """Format the raw LLM response into a well-structured HTML output"""
        try:
            # Extract sections using regex
            summary_match = re.search(r'SUMMARY:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            content_match = re.search(r'CONTENT:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            style_match = re.search(r'STYLE NOTES:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            inspiration_match = re.search(r'INSPIRATION:\s*(.+?)(?=\n|$)', raw_response, re.DOTALL)

            # Format each section
            formatted_response = []
            
            # Summary section
            if summary_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #9C27B0; margin-bottom: 0.5rem;">Summary</h2>'
                    f'<div>{summary_match.group(1).strip()}</div>'
                    '</div>'
                )

            # Main content section
            if content_match:
                content = content_match.group(1).strip()
                # Format paragraphs
                paragraphs = content.split('\n')
                formatted_content = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #9C27B0; margin-bottom: 0.5rem;">Content</h2>'
                    f'<div>{formatted_content}</div>'
                    '</div>'
                )

            # Style notes section
            if style_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem; padding: 1rem; background-color: #f8f9fa; border-left: 4px solid #9C27B0;">'
                    f'<h2 style="color: #9C27B0; margin-bottom: 0.5rem;">Style Notes</h2>'
                    f'<div>{style_match.group(1).strip()}</div>'
                    '</div>'
                )

            # Inspiration section
            if inspiration_match:
                inspiration = inspiration_match.group(1).strip().split('\n')
                formatted_inspiration = (
                    '<div style="margin-bottom: 1.5rem;">'
                    '<h2 style="color: #9C27B0; margin-bottom: 0.5rem;">Inspiration</h2>'
                    '<ul style="margin: 0; padding-left: 1.5rem;">'
                )
                for source in inspiration:
                    source = source.strip()
                    if source:
                        formatted_inspiration += f'<li>{source}</li>'
                formatted_inspiration += '</ul></div>'
                formatted_response.append(formatted_inspiration)

            return '\n'.join(formatted_response)
        except Exception as e:
            # Fallback to raw response if formatting fails
            return f"<pre>{raw_response}</pre>"

    def _get_system_prompt(self) -> str:
        """Return the system prompt for the creative writer role"""
        return self._system_prompt

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        try:
            # Extract sections using regex
            summary = re.search(r'SUMMARY:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            content = re.search(r'CONTENT:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            style = re.search(r'STYLE NOTES:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            inspiration = re.search(r'INSPIRATION:\s*(.+?)(?=\n|$)', response, re.DOTALL)

            return {
                'summary': summary.group(1).strip() if summary else '',
                'content': content.group(1).strip() if content else '',
                'style_notes': style.group(1).strip() if style else '',
                'inspiration': inspiration.group(1).strip().split('\n') if inspiration else []
            }
        except Exception as e:
            # Return empty structure if parsing fails
            return {
                'summary': '',
                'content': '',
                'style_notes': '',
                'inspiration': []
            }

    def get_search_context(self) -> str:
        """Return context for web searches"""
        return """
        Creative writing examples, storytelling techniques, narrative structures,
        writing guides, literary devices, and stylistic elements. Focus on sources
        that showcase engaging writing and creative expression.
        """

    async def process_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Process the query and return a creative response with metrics"""
        # Get search results and metrics
        search_results, metrics, confidence_score, confidence_reasons = await self.web_search.search(
            query, 
            role_context=self.get_search_context()
        )
        
        # Get LLM response
        llm_response = await self.llm.get_response(
            system_prompt=self.system_prompt,
            user_query=query,
            search_results=search_results,
            role_parser=self.parse_llm_response
        )
        
        # Format and return the response with metrics
        formatted_response = f"""
# <span style='font-size: 2em'>Creative Writing</span>

{llm_response.raw_response}

### Inspiration Sources
"""
        # Add evidence points from search results
        seen_urls = set()  # Track seen URLs to avoid duplicates
        evidence_points = []
        
        for result in search_results:
            # Skip if we've seen this URL before
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            
            # Add evidence point
            title = result.title.replace(" - Wikipedia", "")  # Clean up Wikipedia titles
            evidence_points.append({
                'title': title,
                'url': result.url,
                'description': result.description
            })
        
        # Add formatted evidence points
        for i, point in enumerate(evidence_points, 1):
            formatted_response += f"{i}. **[{point['title']}]({point['url']})**\n"
            formatted_response += f"   _{point['description']}_\n\n"
        
        return formatted_response, metrics

    def get_ui_components(self) -> Dict[str, Any]:
        """Get UI components specific to the creative writer role"""
        return {
            'input_label': 'What would you like me to write about?',
            'input_help': 'I can help with creative writing, content creation, or storytelling.',
            'input_placeholder': 'Example: "Write a story about space exploration" or "Create content about sustainable living"',
            'submit_label': 'Generate Creative Content'
        }
