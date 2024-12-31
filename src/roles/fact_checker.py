import re
from typing import Any, Dict, List, Tuple
from .base_role import BaseRole
from ..web_search import SearchMetrics

class fact_checker(BaseRole):
    """
    Fact Checker role that evaluates claims and identifies opinions.
    Provides confidence scoring and distinguishes between factual and opinion-based queries.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Fact Checker"
        self.description = "Evaluates claims and provides evidence-based responses"
        self.system_prompt = """You are a Fact Checker AI assistant focused on:
1. Evaluating claims with clear confidence levels
2. Distinguishing between facts and opinions
3. Providing evidence-based responses
4. Cross-referencing multiple sources
5. Highlighting potential misinformation

For opinion-based questions:
- Clearly label them as subjective
- Provide balanced perspectives from various sources
- Explain why the topic is subjective
- Still provide factual context where possible

Always:
- State your confidence level and explain why
- Cite sources when making claims
- Be transparent about limitations
- Correct misinformation when found"""
    
    def _get_system_prompt(self) -> str:
        """Return the system prompt for the fact checker role"""
        return """You are a Fact Checker AI assistant focused on:
1. Evaluating claims with clear confidence levels
2. Distinguishing between facts and opinions
3. Providing evidence-based responses
4. Cross-referencing multiple sources
5. Highlighting potential misinformation

For opinion-based questions:
- Clearly label them as subjective
- Provide balanced perspectives from various sources
- Explain why the topic is subjective
- Still provide factual context where possible

Always:
- State your confidence level and explain why
- Cite sources when making claims
- Be transparent about limitations
- Correct misinformation when found

Structure your responses as follows:
VERDICT: [TRUE/MOSTLY TRUE/MIXED/MOSTLY FALSE/FALSE]
CONFIDENCE LEVEL: [Very High/High/Moderate/Low/Very Low]
OPINION WARNING: [If applicable, explain why this is an opinion-based question]
EXPLANATION: [Clear explanation of your verdict]
CONTEXT: [Additional context or nuance]
REFERENCES: [List of sources used, one per line]"""
    
    def is_opinion_based(self, query: str) -> bool:
        """
        Determine if a question is opinion-based.
        
        Looks for subjective indicators like:
        - Personal preference words (best, favorite, better, worse)
        - Moral/ethical judgments (should, right, wrong)
        - Aesthetic judgments (beautiful, ugly, nice)
        - Emotional responses (feel, think about, believe)
        """
        opinion_indicators = [
            r"\b(best|better|worst|worse|favorite|prefer)\b",
            r"\b(should|ought|right|wrong|good|bad)\b",
            r"\b(beautiful|ugly|nice|pleasant|attractive)\b",
            r"\b(feel|think|believe|opinion|viewpoint)\b",
            r"\b(popular|controversial|debatable)\b"
        ]
        
        return any(re.search(pattern, query.lower()) for pattern in opinion_indicators)
    
    def format_confidence_level(self, confidence_score: float, reasons: List[str]) -> str:
        """Format confidence level and reasons into a readable string"""
        if confidence_score >= 0.9:
            level = "Very High"
        elif confidence_score >= 0.7:
            level = "High"
        elif confidence_score >= 0.5:
            level = "Moderate"
        elif confidence_score >= 0.3:
            level = "Low"
        else:
            level = "Very Low"
        
        return f"🎯 **Confidence Level: {level}**\n*{', '.join(reasons)}*\n"
    
    def format_response(self, raw_response: str) -> str:
        """Format the raw LLM response into a well-structured HTML output"""
        try:
            # Extract sections using regex
            verdict_match = re.search(r'VERDICT:\s*(.+?)(?=\n|$)', raw_response)
            confidence_match = re.search(r'CONFIDENCE LEVEL:\s*(.+?)(?=\n|$)', raw_response)
            explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=\n|$)', raw_response)
            context_match = re.search(r'CONTEXT:\s*(.+?)(?=\n|$)', raw_response)
            references_match = re.search(r'REFERENCES:\s*(.+?)(?=\n|$)', raw_response, re.DOTALL)

            # Format each section
            formatted_response = []
            
            # Error icon for false claims
            verdict = verdict_match.group(1).strip() if verdict_match else "UNKNOWN"
            if verdict.upper() == "FALSE":
                formatted_response.append('<div class="error-message" style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;"><span style="color: #FF4B4B; font-size: 24px;">⚠</span><span style="color: #FF4B4B;">{}</span></div>'.format(raw_response.split('\n')[0]))

            # Verdict as a simple statement
            formatted_response.append(f'<div style="margin: 16px 0;"><strong>{verdict}</strong></div>')

            # Explanation section
            if explanation_match:
                formatted_response.append('<h2 style="margin: 24px 0 16px;">Explanation</h2>')
                formatted_response.append(f'<div style="margin-bottom: 16px;">{explanation_match.group(1).strip()}</div>')

            # Additional Context section
            if context_match:
                formatted_response.append('<h2 style="margin: 24px 0 16px;">Additional Context</h2>')
                formatted_response.append(f'<div style="margin-bottom: 16px;">{context_match.group(1).strip()}</div>')

            # References section
            if references_match:
                formatted_response.append('<h2 style="margin: 24px 0 16px;">References</h2>')
                references = references_match.group(1).strip().split('\n')
                for i, ref in enumerate(references, 1):
                    ref = ref.strip()
                    if ref:
                        # Extract URL if present
                        url_match = re.search(r'- (https?://\S+)', ref)
                        if url_match:
                            url = url_match.group(1)
                            source_name = ref.split('-')[0].strip()
                            formatted_response.append(f'{i}. {source_name} - <a href="{url}" target="_blank">{url}</a><br>')
                        else:
                            formatted_response.append(f'{i}. {ref}<br>')

            return '\n'.join(formatted_response)
        except Exception as e:
            # Fallback to raw response if formatting fails
            return f"<pre>{raw_response}</pre>"
    
    async def process_query(self, query: str) -> Tuple[str, SearchMetrics]:
        """Process the query and return a response with confidence level and opinion identification."""
        # Get search results and confidence metrics
        search_results, metrics, confidence_score, confidence_reasons = await self.web_search.search(
            query, 
            role_context=self.get_search_context()
        )
        
        # Format prompt with search results and confidence info
        prompt = (
            f"You are a fact-checking AI. Evaluate this claim: '{query}'\n\n"
            "Format your response exactly like this:\n"
            "1. Start with 'Claim Evaluation: [the claim]'\n"
            "2. State 'VERDICT: [TRUE/FALSE]'\n"
            "3. Add 'EXPLANATION: [detailed explanation]'\n"
            "4. Include 'CONTEXT: [additional context]'\n"
            "5. End with 'REFERENCES: [numbered list of sources]'\n\n"
            f"Search Results (Confidence Score: {confidence_score:.2f}):\n"
            f"Confidence Reasons: {', '.join(confidence_reasons)}\n\n"
        )
        
        for i, result in enumerate(search_results, 1):
            prompt += f"{i}. Title: {result.title}\n"
            prompt += f"   Description: {result.description}\n"
            if result.url:
                prompt += f"   Source: {result.url}\n"
            prompt += f"   Relevance Score: {result.relevance_score:.2f}\n\n"
        
        # Get LLM response
        llm_response = await self.llm.get_response(
            system_prompt=self.system_prompt,
            user_query=query,
            search_results=search_results,
            role_parser=self.parse_llm_response
        )
        
        # Format and return the response with metrics
        formatted_response = f"""
# <span style='font-size: 2em'>Fact Check Results</span>

### Claim Evaluation
**"{query}"**

### Verdict
{llm_response.raw_response}

### Key Evidence
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
    
    async def generate_response(self, query: str, conversation_history: List[str] = None) -> str:
        """
        Generate a response to the user's query.
        This is the main entry point for processing queries.
        """
        response, _ = await self.process_query(query)
        
        # Add to conversation history if provided
        if conversation_history is not None:
            conversation_history.extend([f"User: {query}", f"Assistant: {response}"])
        
        return response
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Get UI components specific to the fact checker role"""
        return {
            'input_label': 'Enter the statement to fact-check:',
            'input_help': 'Provide a clear, specific statement that you want to verify.',
            'input_placeholder': 'Example: "The Earth is flat" or "Coffee is the world\'s most traded commodity"',
            'submit_label': 'Verify Statement',
            'results_container': {
                'sections': [
                    {
                        'title': 'Verdict',
                        'content_key': 'verdict',
                        'style': {'color': lambda x: {
                            'TRUE': '#28a745',
                            'MOSTLY TRUE': '#5cb85c',
                            'MIXED': '#ffc107',
                            'MOSTLY FALSE': '#dc3545',
                            'FALSE': '#dc3545'
                        }.get(x, '#6c757d')}
                    },
                    {
                        'title': 'Confidence Level',
                        'content_key': 'confidence_level'
                    },
                    {
                        'title': 'Opinion Warning',
                        'content_key': 'opinion_warning'
                    },
                    {
                        'title': 'Explanation',
                        'content_key': 'explanation'
                    },
                    {
                        'title': 'Additional Context',
                        'content_key': 'context'
                    },
                    {
                        'title': 'Sources',
                        'content_key': 'references',
                        'type': 'list'
                    }
                ]
            }
        }
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        sections = {
            'verdict': '',
            'explanation': '',
            'context': '',
            'references': [],
            'confidence_level': '',
            'opinion_warning': ''
        }
        
        current_section = None
        section_content = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('VERDICT:'):
                current_section = 'verdict'
                sections['verdict'] = line.replace('VERDICT:', '').strip()
            elif line.startswith('EXPLANATION:'):
                current_section = 'explanation'
                section_content = []
            elif line.startswith('CONTEXT:'):
                current_section = 'context'
                section_content = []
            elif line.startswith('REFERENCES:'):
                current_section = 'references'
                section_content = []
            elif line.startswith('CONFIDENCE LEVEL:'):
                current_section = 'confidence_level'
                sections['confidence_level'] = line.replace('CONFIDENCE LEVEL:', '').strip()
            elif line.startswith('OPINION WARNING:'):
                current_section = 'opinion_warning'
                sections['opinion_warning'] = line.replace('OPINION WARNING:', '').strip()
            elif current_section:
                section_content.append(line)
            
            if section_content:
                if current_section == 'explanation':
                    sections['explanation'] = '\n'.join(section_content)
                elif current_section == 'context':
                    sections['context'] = '\n'.join(section_content)
                elif current_section == 'references':
                    sections['references'] = section_content
        
        return sections
