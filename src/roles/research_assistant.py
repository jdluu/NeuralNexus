from typing import Any, Dict, Tuple
import re
from .base_role import BaseRole
from ..web_search import SearchMetrics

class research_assistant(BaseRole):
    """Research Assistant Role
    
    Specializes in comprehensive research and analysis, providing
    well-structured responses with citations and academic rigor.
    """
    def _get_system_prompt(self) -> str:
        return '''You are NeuralNexus's expert research assistant. Your role is to provide comprehensive, 
well-researched answers to questions using both search results and your knowledge.

Structure your response exactly as follows:
SUMMARY: [Brief, clear answer to the question]
ANALYSIS: [Detailed explanation with multiple sections]
KEY_POINTS: [Main takeaways, one per line with bullet points]
SOURCES: [List of references used, one per line]'''

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        sections = {
            'summary': '',
            'analysis': '',
            'key_points': [],
            'sources': []
        }
        
        current_section = None
        
        for line in response.split('\n'):
            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                sections['summary'] = line.replace('SUMMARY:', '').strip()
            elif line.startswith('ANALYSIS:'):
                current_section = 'analysis'
                sections['analysis'] = line.replace('ANALYSIS:', '').strip()
            elif line.startswith('KEY_POINTS:'):
                current_section = 'key_points'
            elif line.startswith('SOURCES:'):
                current_section = 'sources'
            elif line.strip() and current_section:
                if current_section == 'analysis':
                    sections['analysis'] += '\n' + line
                elif current_section == 'key_points' and line.strip().startswith('- '):
                    sections['key_points'].append(line.strip()[2:])
                elif current_section == 'sources' and line.strip().startswith('- '):
                    sections['sources'].append(line.strip()[2:])
        
        return sections

    def format_response(self, raw_response: str) -> str:
        """Format the response into HTML"""
        try:
            # Parse the response
            sections = self.parse_llm_response(raw_response)
            
            # Build HTML components
            html_parts = []
            
            # Summary section
            if sections['summary']:
                html_parts.append(
                    '<div style="margin-bottom: 1.5rem; padding: 1rem; background-color: #f0f7ff; border-radius: 0.5rem;">'
                    f'<h2 style="color: #1976D2; margin-bottom: 0.5rem;">Summary</h2>'
                    f'<div>{sections["summary"]}</div>'
                    '</div>'
                )
            
            # Analysis section
            if sections['analysis']:
                html_parts.append(
                    '<div style="margin-bottom: 1.5rem;">'
                    f'<h2 style="color: #1976D2; margin-bottom: 0.5rem;">Analysis</h2>'
                    f'<div>{sections["analysis"]}</div>'
                    '</div>'
                )
            
            # Key Points section
            if sections['key_points']:
                key_points_html = (
                    '<div style="margin-bottom: 1.5rem; padding: 1rem; background-color: #f5f5f5; border-radius: 0.5rem;">'
                    '<h2 style="color: #1976D2; margin-bottom: 0.5rem;">Key Points</h2>'
                    '<ul style="margin: 0; padding-left: 1.5rem;">'
                )
                for point in sections['key_points']:
                    key_points_html += f'<li>{point}</li>'
                key_points_html += '</ul></div>'
                html_parts.append(key_points_html)
            
            # Sources section
            if sections['sources']:
                sources_html = (
                    '<div style="margin-bottom: 1.5rem;">'
                    '<h2 style="color: #1976D2; margin-bottom: 0.5rem;">Sources</h2>'
                    '<ul style="margin: 0; padding-left: 1.5rem;">'
                )
                for source in sections['sources']:
                    # Check if it's a URL and make it clickable if it is
                    if source.startswith(('http://', 'https://')):
                        sources_html += f'<li><a href="{source}" target="_blank">{source}</a></li>'
                    else:
                        sources_html += f'<li>{source}</li>'
                sources_html += '</ul></div>'
                html_parts.append(sources_html)
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            # Fallback to raw response if formatting fails
            return f"<pre>{raw_response}</pre>"

    async def process_query(self, query: str) -> Tuple[str, SearchMetrics]:
        """Process the query and return a research response"""
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
# <span style='font-size: 2em'>Research Results</span>

{llm_response.raw_response}

### Sources Used
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
        return {
            'layout': 'full_width',
            'components': {
                'summary': {
                    'type': 'highlighted_text',
                    'style': {
                        'padding': '1rem',
                        'background': '#f0f7ff',
                        'border_radius': '0.5rem',
                        'margin_bottom': '1rem'
                    }
                },
                'analysis': {
                    'type': 'markdown',
                    'style': {
                        'margin_top': '1rem',
                        'margin_bottom': '1rem'
                    }
                },
                'key_points': {
                    'type': 'bullet_list',
                    'style': {
                        'background': '#f5f5f5',
                        'padding': '1rem',
                        'border_radius': '0.5rem'
                    }
                },
                'sources': {
                    'type': 'collapsible_references',
                    'style': {
                        'margin_top': '1rem'
                    }
                }
            }
        }
