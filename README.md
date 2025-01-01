# NeuralNexus Hub

A versatile AI assistant platform that combines powerful web search capabilities with specialized AI roles to provide comprehensive assistance for various tasks. Each role is expertly designed to handle specific types of queries and provide tailored responses.

## Features

### Multiple Specialized AI Roles

1. **🔍 Research Assistant**

   - Comprehensive research across multiple sources
   - Synthesis of complex information
   - Clear and structured presentation of findings
   - Citation of reliable sources

2. **✓ Fact Checker**

   - Verification of claims against reliable sources
   - Analysis of source credibility
   - Clear verdict presentation
   - Evidence-based explanations

3. **💻 Technical Expert**

   - In-depth technical explanations
   - Code analysis and review
   - Best practices guidance
   - Implementation recommendations

4. **✍️ Creative Writer**
   - Creative content generation
   - Style and tone adaptation
   - Narrative development
   - Writing technique suggestions

### Core Capabilities

- Real-time web search integration
- AI-powered analysis and response generation
- Source deduplication and validation
- Modern, responsive UI with accessibility features
- Comprehensive error handling and logging

## Prerequisites

- Python 3.10 or higher
- Web Search API key (for search functionality)
- LLM API key (for AI response generation)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/jdluu/NeuralNexus.git
cd NeuralNexus
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:

```env
GLHF_API_KEY=your_glhf_api_key_here
BRAVE_API_KEY=your_brave_api_key_here
LLM_MODEL=hf:meta-llama/Llama-3.3-70B-Instruct
```

## Usage

Run the Streamlit web interface:

```bash
streamlit run streamlit_ui.py
```

The interface will guide you through:

1. Selecting the most appropriate AI role for your task
2. Entering your query or request
3. Viewing the AI's response with relevant sources and information

## Project Structure

- `src/roles/`: Specialized AI role implementations
  - `research_assistant.py`: Comprehensive research and analysis
  - `fact_checker.py`: Claim verification and evidence assessment
  - `technical_expert.py`: Technical guidance and implementation help
  - `creative_writer.py`: Creative content generation and writing assistance
- `src/`: Core functionality

  - `web_search.py`: Web search integration
  - `llm_handler.py`: Language model interaction
  - `base_role.py`: Base class for AI roles

- `streamlit_ui.py`: Web interface implementation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Web Search API providers for search capabilities
- LLM providers for AI model access
- Streamlit for the web interface framework
- Brave Search API for web search capabilities
- GLHF.chat for AI model access
- logfire for comprehensive logging
