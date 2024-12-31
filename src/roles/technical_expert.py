import re
from typing import Any, Dict, List, Tuple
from .base_role import BaseRole
from abc import ABC, abstractmethod

class technical_expert(BaseRole):
    """
    Technical Expert role that provides detailed technical explanations and analysis.
    Focuses on technical accuracy, implementation details, and best practices.
    """
    
    def __init__(self):
        self.name = "Technical Expert"
        self.description = "Provides detailed technical explanations and implementation guidance"
        self._system_prompt = """You are a Technical Expert AI assistant focused on:
1. Providing accurate technical explanations
2. Explaining complex concepts clearly
3. Offering implementation guidance
4. Discussing best practices
5. Analyzing technical trade-offs

When answering questions:
- Start with a high-level overview
- Break down complex topics into digestible parts
- Include relevant code examples when appropriate
- Cite specific documentation and resources
- Explain technical trade-offs and alternatives

Always:
- Be precise and technically accurate
- Use industry-standard terminology
- Reference official documentation
- Highlight important considerations
- Address potential pitfalls"""
        super().__init__()

    def _get_system_prompt(self) -> str:
        """Return the system prompt for the technical expert role"""
        return self._system_prompt

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        try:
            # Extract sections using regex
            overview = re.search(r'OVERVIEW:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            details = re.search(r'TECHNICAL DETAILS:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            implementation = re.search(r'IMPLEMENTATION:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            considerations = re.search(r'CONSIDERATIONS:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
            references = re.search(r'REFERENCES:\s*(.+?)(?=\n|$)', response, re.DOTALL)

            return {
                'overview': overview.group(1).strip() if overview else '',
                'technical_details': details.group(1).strip() if details else '',
                'implementation': implementation.group(1).strip() if implementation else '',
                'considerations': considerations.group(1).strip() if considerations else '',
                'references': references.group(1).strip().split('\n') if references else []
            }
        except Exception as e:
            # Return empty structure if parsing fails
            return {
                'overview': '',
                'technical_details': '',
                'implementation': '',
                'considerations': '',
                'references': []
            }

    def format_response(self, raw_response: str) -> str:
        """Format the raw LLM response into a well-structured HTML output"""
        try:
            # Extract sections using regex
            overview_match = re.search(r'OVERVIEW:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            details_match = re.search(r'TECHNICAL DETAILS:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            implementation_match = re.search(r'IMPLEMENTATION:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            considerations_match = re.search(r'CONSIDERATIONS:\s*(.+?)(?=\n\n|$)', raw_response, re.DOTALL)
            references_match = re.search(r'REFERENCES:\s*(.+?)(?=\n|$)', raw_response, re.DOTALL)

            # Format each section
            formatted_response = []
            
            # Overview section
            if overview_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #2196F3; margin-bottom: 0.5rem;">Overview</h2>'
                    f'<div>{overview_match.group(1).strip()}</div>'
                    '</div>'
                )

            # Technical Details section
            if details_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #2196F3; margin-bottom: 0.5rem;">Technical Details</h2>'
                    f'<div>{details_match.group(1).strip()}</div>'
                    '</div>'
                )

            # Implementation section
            if implementation_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #2196F3; margin-bottom: 0.5rem;">Implementation</h2>'
                    f'<div>{implementation_match.group(1).strip()}</div>'
                    '</div>'
                )

            # Considerations section
            if considerations_match:
                formatted_response.append(
                    '<div style="margin-bottom: 1.5rem; padding: 1rem; background-color: #f8f9fa; border-left: 4px solid #2196F3;">'
                    f'<h2 style="color: #2196F3; margin-bottom: 0.5rem;">Important Considerations</h2>'
                    f'<div>{considerations_match.group(1).strip()}</div>'
                    '</div>'
                )

            # References section
            if references_match:
                references = references_match.group(1).strip().split('\n')
                formatted_refs = (
                    '<div style="margin-bottom: 1.5rem;">'
                    '<h2 style="color: #2196F3; margin-bottom: 0.5rem;">References</h2>'
                    '<ul style="margin: 0; padding-left: 1.5rem;">'
                )
                for ref in references:
                    ref = ref.strip()
                    if ref:
                        # Check if it's a URL and make it clickable if it is
                        if ref.startswith(('http://', 'https://')):
                            formatted_refs += f'<li><a href="{ref}" target="_blank">{ref}</a></li>'
                        else:
                            formatted_refs += f'<li>{ref}</li>'
                formatted_refs += '</ul></div>'
                formatted_response.append(formatted_refs)

            return '\n'.join(formatted_response)
        except Exception as e:
            # Fallback to raw response if formatting fails
            return f"<pre>{raw_response}</pre>"

    def get_search_context(self) -> str:
        """Return context for web searches"""
        return """
        Technical documentation, API references, implementation guides, best practices,
        and academic papers related to software development, computer science, and engineering.
        Prioritize official documentation, technical blogs, and peer-reviewed sources.
        """

    async def process_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Process the query and return a technical response with metrics"""
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
# <span style='font-size: 2em'>Technical Analysis</span>

{llm_response.raw_response}

### References
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
        """Get UI components specific to the technical expert role"""
        return {
            'input_label': 'What technical topic would you like to explore?',
            'input_help': 'Ask about programming concepts, system design, or technical implementations.',
            'input_placeholder': 'Example: "How does Docker containerization work?" or "Explain OAuth 2.0"',
            'submit_label': 'Get Technical Analysis'
        }
