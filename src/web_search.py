from __future__ import annotations

import os
import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from dataclasses import dataclass
import statistics

import logfire
from httpx import AsyncClient, HTTPError, TimeoutException
from dotenv import load_dotenv
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class SearchMetrics:
    """Metrics for search performance tracking"""
    total_time: float
    cache_hit: bool
    results_count: int
    error: Optional[str] = None

class SearchResult(BaseModel):
    """Model for search results"""
    title: str
    url: str
    description: str
    query_time: float
    relevance_score: float = 1.0  # Default relevance score

class WebSearch:
    def __init__(self):
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
        if not self.brave_api_key:
            raise ValueError("BRAVE_API_KEY environment variable is required")
        
        # Configure client session with optimal settings
        self.timeout = 10.0
        self.max_retries = 2
        self.concurrent_limit = 3
        self._semaphore = asyncio.Semaphore(self.concurrent_limit)

    def _sanitize_query(self, query: str) -> str:
        """Sanitize the search query to prevent injection attacks."""
        return ' '.join(query.split())

    @lru_cache(maxsize=100)
    def _get_cached_results(self, query: str) -> Optional[List[SearchResult]]:
        """Cache wrapper for search results"""
        return None  # Actual implementation will store results

    async def _make_request(self, client: AsyncClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single search request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with self._semaphore:
                    response = await client.get(
                        'https://api.search.brave.com/res/v1/web/search',
                        headers={
                            'X-Subscription-Token': self.brave_api_key,
                            'Accept': 'application/json',
                        },
                        params=params,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    return response.json()
            except TimeoutException:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
            except HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    raise

    def _calculate_relevance(self, result: Dict[str, Any], query_terms: set) -> float:
        """Calculate relevance score for a search result"""
        text = f"{result['title']} {result['description']}".lower()
        query_terms_lower = {term.lower() for term in query_terms}
        
        # Calculate term frequency
        term_count = sum(1 for term in query_terms_lower if term in text)
        # Normalize by number of terms
        relevance = term_count / len(query_terms_lower) if query_terms_lower else 0
        
        # Boost for exact phrase matches
        if ' '.join(query_terms_lower) in text:
            relevance *= 1.5
            
        return min(relevance, 1.0)  # Cap at 1.0

    def assess_source_quality(self, source: dict) -> float:
        """
        Assess the quality of a source based on various factors.
        Returns a score between 0 and 1.
        """
        quality_score = 0.0
        
        # Domain reputation (example scoring)
        reputable_domains = {
            'edu': 0.9,  # Educational institutions
            'gov': 0.9,  # Government sites
            'org': 0.7,  # Non-profit organizations
            'com': 0.5,  # Commercial sites (baseline)
        }
        
        domain = source.get('domain', '')
        domain_ext = domain.split('.')[-1]
        quality_score += reputable_domains.get(domain_ext, 0.3)
        
        # Source freshness
        current_year = datetime.now().year
        pub_year = source.get('publication_year', current_year)
        years_old = current_year - pub_year
        freshness_score = max(0, 1 - (years_old / 10))  # Linearly decrease over 10 years
        quality_score += freshness_score * 0.3
        
        # Source type (if available)
        source_types = {
            'academic': 0.9,
            'news': 0.6,
            'blog': 0.4,
            'forum': 0.3,
        }
        source_type = source.get('type', 'unknown')
        quality_score += source_types.get(source_type, 0.2)
        
        # Normalize final score to 0-1 range
        return min(1.0, quality_score / 2.0)
    
    def calculate_confidence(self, sources: List[dict]) -> Tuple[float, List[str]]:
        """
        Calculate overall confidence score and supporting reasons.
        Returns (confidence_score, list_of_reasons)
        """
        if not sources:
            return 0.0, ["No sources found"]
        
        # Calculate individual source scores
        source_scores = [self.assess_source_quality(source) for source in sources]
        
        # Overall confidence metrics
        avg_score = sum(source_scores) / len(source_scores)
        consistency = 1.0 - statistics.stdev(source_scores) if len(source_scores) > 1 else 0.5
        num_sources_score = min(1.0, len(sources) / 5)  # Max score at 5+ sources
        
        # Weighted confidence score
        confidence_score = (
            avg_score * 0.4 +          # Source quality
            consistency * 0.3 +         # Information consistency
            num_sources_score * 0.3     # Number of sources
        )
        
        # Generate reasons
        reasons = []
        if avg_score > 0.7:
            reasons.append("High-quality sources found")
        if consistency > 0.7:
            reasons.append("Consistent information across sources")
        if num_sources_score > 0.6:
            reasons.append(f"Multiple sources ({len(sources)}) corroborate the information")
        
        return confidence_score, reasons
    
    async def search(self, query: str, role_context: str) -> tuple[List[SearchResult], SearchMetrics, float, List[str]]:
        """
        Perform a web search with context from the role.
        
        Args:
            query: The user's query
            role_context: The role's system prompt or context to guide the search
        
        Returns:
            Tuple of (List[SearchResult], SearchMetrics, confidence_score, confidence_reasons)
        """
        start_time = time.time()
        metrics = SearchMetrics(
            total_time=0,
            cache_hit=False,
            results_count=0
        )

        try:
            # Check cache first
            cached_results = self._get_cached_results(query)
            if cached_results:
                metrics.cache_hit = True
                metrics.total_time = time.time() - start_time
                metrics.results_count = len(cached_results)
                return cached_results, metrics, 0.0, ["No confidence assessment"]

            # Enhance query based on role context
            enhanced_query = self._enhance_query(query, role_context)
            sanitized_query = self._sanitize_query(enhanced_query)
            query_terms = set(sanitized_query.split())

            # Prepare search parameters
            params = {
                'q': sanitized_query,
                'count': 10,
                'freshness': 'pw',  # Past week
                'text_decorations': False,
                'text_format': 'raw'
            }

            async with AsyncClient() as client:
                results = await self._make_request(client, params)
                
                search_results = []
                sources = []
                for result in results.get('web', {}).get('results', []):
                    relevance = self._calculate_relevance(result, query_terms)
                    search_results.append(
                        SearchResult(
                            title=result['title'],
                            url=result['url'],
                            description=result['description'],
                            query_time=time.time() - start_time,
                            relevance_score=relevance
                        )
                    )
                    sources.append({
                        'domain': result['url'].split('/')[2],
                        'publication_year': result.get('date_published', datetime.now().year),
                        'type': 'unknown'  # Add type detection logic here
                    })
                
                # Sort by relevance
                search_results.sort(key=lambda x: x.relevance_score, reverse=True)
                
                metrics.total_time = time.time() - start_time
                metrics.results_count = len(search_results)
                
                confidence_score, confidence_reasons = self.calculate_confidence(sources)
                
                return search_results, metrics, confidence_score, confidence_reasons

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            metrics.error = str(e)
            metrics.total_time = time.time() - start_time
            return [], metrics, 0.0, ["No confidence assessment"]

    def _enhance_query(self, query: str, role_context: str) -> str:
        """
        Enhance the search query based on the role's context.
        This could be expanded to use LLM for better query formulation.
        """
        # Extract key terms from role context to enhance search
        role_terms = role_context.lower()
        
        # Define search modifiers based on role context
        modifiers = {
            'fact check': ['fact check', 'verify', 'evidence'],
            'research': ['research paper', 'academic', 'study'],
            'technical': ['technical documentation', 'api', 'implementation'],
            'news': ['news', 'recent', 'current events'],
            'analysis': ['analysis', 'insights', 'expert opinion']
        }
        
        # Find matching modifiers
        query_modifiers = []
        for key, terms in modifiers.items():
            if any(term in role_terms for term in terms):
                query_modifiers.extend(terms[:1])  # Take only first term to avoid over-modification
        
        # Combine query with modifiers
        if query_modifiers:
            return f"{' '.join(query_modifiers)} {query}"
        return query
