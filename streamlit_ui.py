from dotenv import load_dotenv
import streamlit as st
import asyncio
import os
import re
import time
import logging
import importlib
import inspect
from typing import Dict, Any, List, Tuple

from src.roles.base_role import BaseRole
from src.web_search import WebSearch, SearchMetrics
from src.llm_handler import LLMHandler
from src.roles.fact_checker import fact_checker
from src.roles.technical_expert import technical_expert
from src.roles.creative_writer import creative_writer
from src.roles.research_assistant import research_assistant

# Configure page layout
st.set_page_config(
    page_title="NeuralNexus Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
AI_DISCLAIMER = """
⚠️ *Note: While this AI assistant strives for accuracy, it may occasionally make mistakes. 
Always verify critical information from multiple reliable sources.*
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Custom CSS for UI styling
st.markdown("""
<style>
    /* Fix banner overlap and adjust overall layout */
    .stApp {
        margin-top: 0;
        min-height: auto !important;
    }
    .block-container {
        padding: 4rem 0rem 0rem;
        max-width: 95%;
        min-height: auto !important;
    }
    
    /* Header and text styling */
    h1 {
        margin: 0 0 0.5rem 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        font-size: 2.2em !important;
    }
    h2 {
        margin: 0.5rem 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        font-size: 1.8em !important;
    }
    p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.4 !important;
    }
    
    /* Component spacing */
    .stMarkdown {
        margin: 0.2rem 0 !important;
    }
    .stSelectbox {
        margin: 0.2rem 0 !important;
    }
    .stTextArea {
        margin: 0.2rem 0 !important;
    }
    .stButton {
        margin: 0.2rem 0 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: rgb(255, 75, 75) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-weight: 500 !important;
        border-radius: 0.5rem !important;
        font-size: 1.1em !important;
        width: 200px !important;
        height: 45px !important;
    }
    .stButton > button:hover {
        background-color: rgb(235, 55, 55) !important;
        border-color: rgb(235, 55, 55) !important;
    }
    .stButton > button:active {
        background-color: rgb(215, 35, 35) !important;
        border-color: rgb(215, 35, 35) !important;
    }
    .stButton > button:focus {
        box-shadow: none !important;
    }
    
    /* Improve vertical spacing */
    div[data-testid="stVerticalBlock"] > div {
        margin: 0.2rem 0 !important;
        padding: 0 !important;
    }
    
    /* Make text area taller */
    .stTextArea textarea {
        min-height: 100px !important;
        padding: 0.5rem !important;
    }
    
    /* Role description styling */
    .role-description {
        padding: 0.5rem !important;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 0.5rem;
        margin: 0.5rem 0 !important;
    }
    
    /* Tips section styling */
    .tips-section {
        margin: 0.5rem 0 !important;
        padding: 0.5rem !important;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 0.5rem;
    }
    
    /* Row widget spacing */
    .row-widget {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove footer padding */
    footer {
        display: none !important;
    }
    
    /* Main content area */
    .main > div:last-child {
        padding-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for better responsiveness
st.markdown("""
<style>
    /* Responsive container */
    .main > div {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Responsive text */
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
        p, li { font-size: 0.9rem !important; }
    }
    
    /* Improved accessibility */
    a:focus { outline: 2px solid #2196F3 !important; }
    button:focus { outline: 2px solid #2196F3 !important; }
    
    /* Better contrast */
    .stTextInput > div > div > input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Cache initialization of handlers
@st.cache_resource
def init_handlers():
    return WebSearch(), LLMHandler()

# Cache role loading
@st.cache_data(show_spinner=False, ttl="1h")
def load_roles() -> Dict[str, BaseRole]:
    """Load all available roles"""
    roles_dir = os.path.join(os.path.dirname(__file__), 'src', 'roles')
    roles = {}
    
    # Exclude base_role and __init__
    exclude_files = {'base_role.py', '__init__.py', '__pycache__'}
    
    for filename in os.listdir(roles_dir):
        if filename.endswith('.py') and filename not in exclude_files:
            module_name = filename[:-3]  # Remove .py extension
            module = importlib.import_module(f'src.roles.{module_name}')
            
            # Get the role class (same name as the module)
            role_class = getattr(module, module_name)
            roles[module_name] = role_class()
    
    return roles

def format_role_name(role_name: str) -> str:
    """Format role name for display"""
    # Split by underscore and capitalize each word
    words = role_name.split('_')
    return ' '.join(word.capitalize() for word in words)

def format_role_description(emoji: str, name: str, description: str, capabilities: List[str], ideal_for: str) -> str:
    """Format a role description with consistent styling"""
    return f"""
<div style='margin-bottom: 1rem;'>
    <h3 style='margin-bottom: 0.5rem;'>{emoji} {name}</h3>
    <p style='margin-bottom: 0.5rem;'>{description}</p>
    <ul style='margin-bottom: 0.5rem; padding-left: 1.5rem;'>
        {' '.join(f'<li>{cap}</li>' for cap in capabilities)}
    </ul>
    <p><strong>Ideal for:</strong> {ideal_for}</p>
</div>
"""

def get_role_descriptions() -> Dict[str, str]:
    """Get descriptions for each role"""
    return {
        'research_assistant': format_role_description(
            emoji="🔍",
            name="Research Assistant",
            description="An AI assistant focused on gathering and analyzing information from multiple sources.",
            capabilities=[
                "Comprehensive research across multiple sources",
                "Synthesis of complex information",
                "Clear and structured presentation of findings",
                "Citation of reliable sources"
            ],
            ideal_for="Research projects, literature reviews, and information gathering tasks."
        ),
        'fact_checker': format_role_description(
            emoji="✓",
            name="Fact Checker",
            description="An AI assistant that evaluates claims and provides evidence-based responses.",
            capabilities=[
                "Verification of claims against reliable sources",
                "Analysis of source credibility",
                "Clear verdict presentation",
                "Evidence-based explanations"
            ],
            ideal_for="Fact verification, claim assessment, and source validation."
        ),
        'technical_expert': format_role_description(
            emoji="💻",
            name="Technical Expert",
            description="An AI assistant specializing in technical topics and implementation details.",
            capabilities=[
                "In-depth technical explanations",
                "Code analysis and review",
                "Best practices guidance",
                "Implementation recommendations"
            ],
            ideal_for="Technical questions, code review, and implementation guidance."
        ),
        'creative_writer': format_role_description(
            emoji="✍️",
            name="Creative Writer",
            description="An AI assistant that helps with creative writing and content generation.",
            capabilities=[
                "Creative content generation",
                "Style and tone adaptation",
                "Narrative development",
                "Writing technique suggestions"
            ],
            ideal_for="Creative writing, content creation, and storytelling tasks."
        )
    }

def get_role_tips(role_name: str) -> str:
    """Get role-specific tips"""
    tips = {
        "fact_checker": [
            "Provide the exact claim you want to verify",
            "Include the source of the claim if available",
            "Specify any context that might be relevant",
            "Ask for specific aspects you want fact-checked"
        ],
        "technical_expert": [
            "Include your programming language or technology",
            "Specify version numbers if relevant",
            "Describe what you've already tried",
            "Mention any specific constraints"
        ],
        "creative_writer": [
            "Specify your target audience",
            "Mention the desired tone and style",
            "Include any length requirements",
            "Note any specific themes to include"
        ]
    }
    
    default_tips = [
        "Be clear and specific with your question",
        "Provide relevant context",
        "Break complex questions into smaller parts",
        "Ask for clarification if needed"
    ]
    
    selected_tips = tips.get(role_name, default_tips)
    tips_list = "\n".join(f"- {tip}" for tip in selected_tips)
    
    return f"""💡 **Tips for better results:**
{tips_list}"""

def format_time(seconds: float) -> str:
    """Format time in seconds to a readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}m {seconds:.1f}s"

async def process_with_status_updates(query: str, role: str, status) -> Tuple[SearchMetrics, str]:
    """Process a query with status updates"""
    try:
        # Get role handler
        role_handler = st.session_state.role_handler
        
        # Update status for search phase
        status.update(label="Searching for relevant information...", state="running")
        
        # Process query and get metrics
        search_metrics, llm_response = await role_handler.process_query(query, role)
        
        # Display search completion time immediately after search
        st.markdown(
            '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">'
            f'<span>⚡</span><span style="color: #666;">Search completed in {search_metrics.total_time:.2f}s</span>'
            '</div>',
            unsafe_allow_html=True
        )
        
        # Update status for analysis phase
        status.update(label="Analyzing search results...", state="running")
        
        return search_metrics, llm_response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise

async def process_query(web_search: WebSearch, llm_handler: LLMHandler, 
                       selected_role, query: str) -> tuple[Any, SearchMetrics]:
    """Process a query with search and LLM analysis"""
    # Perform web search
    search_results, metrics, confidence_score, confidence_reasons = await web_search.search(
        query,
        selected_role.get_search_context()
    )
    
    if not search_results:
        return None, metrics
    
    # Process with LLM
    llm_response = await llm_handler.get_response(
        selected_role.system_prompt,
        query,
        search_results,
        selected_role.parse_llm_response
    )
    
    return llm_response, metrics

def display_metrics(metrics: SearchMetrics, llm_time: float):
    """Display performance metrics in a structured way"""
    # Progress bars for timing breakdown
    total_time = metrics.total_time + llm_time
    search_percentage = (metrics.total_time / total_time) * 100
    analysis_percentage = (llm_time / total_time) * 100
    
    st.markdown("### Time Breakdown")
    
    # Search time
    st.markdown(f"Search: {format_time(metrics.total_time)} ({search_percentage:.1f}%)")
    st.progress(search_percentage / 100)
    
    # Analysis time
    st.markdown(f"Analysis: {format_time(llm_time)} ({analysis_percentage:.1f}%)")
    st.progress(analysis_percentage / 100)
    
    # Results summary
    st.markdown("### Results Summary")
    st.markdown(f"Found {metrics.results_count} relevant sources")
    if metrics.results_count > 0:
        st.markdown(f"Average processing time per result: {format_time(total_time / max(1, metrics.results_count))}")

# Role response model
class RoleResponse:
    def __init__(self, role_name: BaseRole, formatted_data: Any, search_results: List[Any], llm_response: Any, search_metrics: SearchMetrics):
        self.role_name = role_name
        self.formatted_data = formatted_data
        self.search_results = search_results
        self.llm_response = llm_response
        self.search_metrics = search_metrics

def display_role_response(response: RoleResponse):
    """Display the role's response with metrics"""
    # Display the formatted response
    if response.formatted_data:
        st.markdown(response.formatted_data, unsafe_allow_html=True)
    
    # Display disclaimer at the bottom
    st.markdown(
        '<div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #333; color: #666; font-size: 0.9em;">' 
        + AI_DISCLAIMER + 
        '</div>', 
        unsafe_allow_html=True
    )

class RoleHandler:
    """Handler for different AI roles"""
    
    def __init__(self):
        self.web_search = WebSearch()
        self.llm_handler = LLMHandler()
        
        # Initialize roles with required services
        self.roles = {
            'research_assistant': self._init_role(research_assistant()),
            'fact_checker': self._init_role(fact_checker()),
            'technical_expert': self._init_role(technical_expert()),
            'creative_writer': self._init_role(creative_writer())
        }
    
    def _init_role(self, role: BaseRole) -> BaseRole:
        """Initialize a role with required services"""
        role.initialize(self.web_search, self.llm_handler)
        return role

    async def process_query(self, query: str, role: str) -> Tuple[SearchMetrics, str]:
        """Process a query using the specified role"""
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")
        
        role_instance = self.roles[role]
        
        # Process the query and get metrics
        response, metrics = await role_instance.process_query(query)
        
        return metrics, response

async def main():
    """Main function to run the Streamlit app"""
    # Initialize handlers
    if 'role_handler' not in st.session_state:
        st.session_state.role_handler = RoleHandler()
    
    # Custom CSS for responsiveness and accessibility
    st.markdown("""
        <style>
        /* Responsive text for mobile */
        @media (max-width: 768px) {
            .stMarkdown h1 { font-size: 1.5rem !important; }
            .stMarkdown h2 { font-size: 1.3rem !important; }
            .stMarkdown p, .stMarkdown li { font-size: 0.9rem !important; }
            .stTextArea textarea { font-size: 0.9rem !important; }
            .stButton button { font-size: 0.9rem !important; }
        }
        
        /* Accessibility improvements */
        .stButton button:focus,
        .stTextArea textarea:focus,
        .stSelectbox select:focus {
            outline: 2px solid #2196F3 !important;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2) !important;
        }
        
        /* Better contrast */
        .stTextArea textarea {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with minimal margins
    st.markdown(
        '<div role="banner">'
        '<h1 style="margin-bottom:0.2rem;">Choose Your AI Assistant</h1>'
        '<p style="margin-bottom:0.2rem;">Select the best assistant for your specific needs:</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Create main columns for the interface with adjusted ratio
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Role selector with accessibility improvements
        selected_role = st.selectbox(
            "Select AI Assistant Role",
            options=list(st.session_state.role_handler.roles.keys()),
            format_func=format_role_name,
            key="role_selector",
            index=0
        )
        
        # Display role description
        if selected_role:
            st.markdown(
                f'<div role="complementary">{get_role_descriptions()[selected_role]}</div>',
                unsafe_allow_html=True
            )
            
            # Display role tips
            with st.expander("💡 Tips", expanded=False):
                st.markdown(get_role_tips(selected_role))
    
    with col2:
        if selected_role:
            # Create a more compact input layout
            st.markdown(
                '<h2 style="font-size: 1.5em; margin: 0.3rem 0;" role="heading">What would you like to know?</h2>',
                unsafe_allow_html=True
            )
            
            # Use columns for input and button
            input_col, button_col = st.columns([4, 1])
            
            with input_col:
                query = st.text_area(
                    "Question or request",
                    label_visibility="collapsed",
                    height=68,
                    placeholder="Enter your question or topic here... Be specific for better results.",
                    help="Type your question or request here. Be as specific as possible for better results."
                )
            
            with button_col:
                st.markdown('<div style="padding-top:0.5rem;">', unsafe_allow_html=True)
                submit = st.button(
                    "Submit",
                    type="primary",
                    disabled=not query,
                    help="Click to submit your question"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Process query when button is clicked
            if submit and query:
                try:
                    # Show processing status with ARIA live region
                    with st.status("Processing...", expanded=True) as status:
                        st.markdown(
                            '<div role="status" aria-live="polite">Processing your request...</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Process query
                        search_metrics, llm_response = await process_with_status_updates(
                            query, selected_role, status
                        )
                        
                        # Show processing complete message
                        total_time = search_metrics.total_time if search_metrics else 0
                        status.update(label=f"Processing complete! ({total_time:.1f}s)")
                        
                        # Create and display role response
                        if llm_response and search_metrics:
                            role_response = RoleResponse(
                                role_name=selected_role,
                                formatted_data=llm_response,
                                search_results=[],
                                llm_response=llm_response,
                                search_metrics=search_metrics
                            )
                            
                            # Display response with ARIA role
                            st.markdown(
                                f'<div role="main">{role_response.formatted_data}</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.error("Failed to process query. Please try again.")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())