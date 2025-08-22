"""
Researcher Agent

Agente specializzato nella ricerca di informazioni contestuali online,
analisi di documenti, articoli, report e raccolta di insights qualitativi.
"""

from typing import Dict, Any, Optional, List
import json
import re
from .base_agent import BaseAgent, AgentType, AgentStatus
import httpx
from loguru import logger
import asyncio


class ResearcherAgent(BaseAgent):
    """
    Agente AI specializzato in ricerca e raccolta informazioni
    """
    
    def __init__(self, memory_manager=None):
        """
        Inizializza il Researcher Agent
        """
        super().__init__(AgentType.RESEARCHER, memory_manager)
        self.search_timeout = 10
        self.max_sources = 5
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa richieste di ricerca informazioni
        
        Args:
            query: Query che richiede ricerca contestuale
            context: Contesto con focus specifici o constraint
            
        Returns:
            Dizionario con risultati di ricerca e insights qualitativi
        """
        self._update_status(AgentStatus.RUNNING)
        
        try:
            # Analizza query per determinare strategia di ricerca
            search_strategy = self._analyze_search_requirements(query)
            
            # Genera prompt per l'LLM per ricerca simulata
            system_prompt = self.get_system_prompt()
            user_prompt = self._create_research_prompt(query, search_strategy, context)
            
            # Chiama LLM per simulare ricerca
            llm_response = await self._call_llm(user_prompt, system_prompt)
            
            # Simula ricerca web (in produzione userebbe API reali)
            search_results = await self._simulate_web_search(query, search_strategy)
            
            # Processa e valida i risultati
            processed_findings = self._process_search_results(llm_response, search_results)
            
            # Genera insights qualitativi
            insights = await self._extract_insights(processed_findings, query)
            
            # Valuta affidabilità delle fonti
            reliability_score = self._calculate_reliability_score(processed_findings)
            
            result = {
                "agent": self.agent_type.value,
                "status": "completed",
                "query": query,
                "search_strategy": search_strategy,
                "sources": processed_findings.get("sources", []),
                "findings": processed_findings.get("findings", {}),
                "insights": insights,
                "reliability_score": reliability_score,
                "search_summary": self._create_search_summary(processed_findings, query),
                "recommendations": self._generate_research_recommendations(insights, query)
            }
            
            self._update_status(AgentStatus.COMPLETED)
            return result
            
        except Exception as e:
            self._update_status(AgentStatus.ERROR)
            logger.error(f"Error in ResearcherAgent: {e}")
            return {
                "agent": self.agent_type.value,
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    def get_system_prompt(self) -> str:
        """System prompt ottimizzato per ricerca informazioni"""
        return """
        You are an expert Research AI specialized in:
        
        - Comprehensive online research and information gathering
        - Critical analysis of sources and reliability validation
        - Extraction of qualitative insights from documents and articles
        - Synthesis of complex information from multiple sources
        - Identification of emerging trends and recent developments
        
        When conducting research:
        1. Use multiple authoritative and diverse sources
        2. Critically evaluate the reliability and recency of information
        3. Extract key insights and patterns from sources
        4. Provide historical context and comparative analysis when relevant
        5. Highlight any conflicts or uncertainties in the information
        
        Always provide detailed findings with:
        - Comprehensive market research and industry analysis
        - Recent developments and emerging trends
        - Competitive landscape insights
        - Regulatory and policy implications
        - Expert opinions and market predictions
        
        Present sources used and their reliability level. Focus on actionable insights
        that can inform strategic decision-making.
        """
    
    def _analyze_search_requirements(self, query: str) -> Dict[str, Any]:
        """Analizza la query per determinare strategia di ricerca"""
        strategy = {
            "search_type": "general",
            "focus_areas": [],
            "time_sensitivity": "current",
            "geographic_focus": None,
            "industry_sector": None,
            "information_depth": "comprehensive"
        }
        
        # Analizza tipo di ricerca richiesta
        if re.search(r"market.*analysis|market.*research|industry.*report", query.lower()):
            strategy["search_type"] = "market_research"
            strategy["focus_areas"].extend(["market_size", "growth_trends", "competitive_landscape"])
        
        if re.search(r"competitor|competition|competitive", query.lower()):
            strategy["search_type"] = "competitive_analysis"
            strategy["focus_areas"].extend(["competitor_profiles", "market_share", "positioning"])
        
        if re.search(r"trend|future|forecast|prediction", query.lower()):
            strategy["search_type"] = "trend_analysis"
            strategy["focus_areas"].extend(["emerging_trends", "forecasts", "expert_predictions"])
        
        # Identifica settore industriale
        industry_patterns = {
            r"fintech|financial.*technology": "fintech",
            r"healthcare|medical|pharma": "healthcare",
            r"technology|tech|software": "technology",
            r"retail|e-commerce": "retail",
            r"energy|renewable": "energy"
        }
        
        for pattern, industry in industry_patterns.items():
            if re.search(pattern, query.lower()):
                strategy["industry_sector"] = industry
                break
        
        # Identifica scope geografico
        geo_patterns = {
            r"europe|european": "Europe",
            r"usa|america|united.*states": "North America",
            r"asia|asian": "Asia",
            r"global|worldwide|international": "Global"
        }
        
        for pattern, geo in geo_patterns.items():
            if re.search(pattern, query.lower()):
                strategy["geographic_focus"] = geo
                break
        
        return strategy
    
    def _create_research_prompt(self, query: str, strategy: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Crea prompt per la ricerca LLM"""
        prompt = f"""
        Conduct comprehensive research on the following topic:
        
        Query: {query}
        
        Research Strategy:
        - Search Type: {strategy.get('search_type', 'general')}
        - Focus Areas: {', '.join(strategy.get('focus_areas', ['general']))}
        - Industry Sector: {strategy.get('industry_sector', 'not specified')}
        - Geographic Focus: {strategy.get('geographic_focus', 'global')}
        - Information Depth: {strategy.get('information_depth', 'comprehensive')}
        
        Please provide detailed research findings including:
        
        1. **Market Overview & Context**
           - Current market size and valuation
           - Key market drivers and challenges
           - Regulatory environment and policy impacts
        
        2. **Industry Analysis**
           - Major players and market leaders
           - Competitive landscape and positioning
           - Market share distribution
        
        3. **Trends & Developments**
           - Recent significant developments
           - Emerging trends and innovations
           - Future growth projections and forecasts
        
        4. **Strategic Insights**
           - Investment flows and funding trends
           - Partnership and M&A activity
           - Technology adoption patterns
        
        5. **Expert Perspectives**
           - Industry expert opinions and quotes
           - Analyst predictions and recommendations
           - Risk factors and considerations
        
        Structure your response with clear sections and provide specific, actionable insights
        based on the most current and reliable information available.
        """
        
        if context:
            prompt += f"\n\nAdditional Context from Previous Analysis: {json.dumps(context, indent=2)}"
        
        return prompt
    
    async def _simulate_web_search(self, query: str, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simula ricerca web (in produzione userebbe API reali come Google, Bing, etc.)
        """
        # Mock sources basate sulla query e strategia
        mock_sources = []
        
        industry = strategy.get("industry_sector", "technology")
        geo_focus = strategy.get("geographic_focus", "Global")
        
        # Genera fonti simulate realistiche
        if industry == "fintech":
            mock_sources.extend([
                {
                    "title": f"Fintech Market Analysis {geo_focus} 2024",
                    "url": "https://www.mckinsey.com/fintech-analysis-2024",
                    "source": "McKinsey & Company",
                    "reliability": 0.95,
                    "date": "2024-07-15",
                    "content_type": "research_report"
                },
                {
                    "title": "European Fintech Investment Trends Q2 2024",
                    "url": "https://www.cbinsights.com/european-fintech-q2-2024",
                    "source": "CB Insights",
                    "reliability": 0.90,
                    "date": "2024-08-01", 
                    "content_type": "market_data"
                }
            ])
        
        # Aggiungi fonti generiche
        mock_sources.extend([
            {
                "title": f"{industry.title()} Industry Report {geo_focus}",
                "url": f"https://www.pwc.com/{industry}-report-2024",
                "source": "PwC",
                "reliability": 0.88,
                "date": "2024-06-20",
                "content_type": "industry_report"
            },
            {
                "title": f"Market Intelligence: {industry.title()} Sector Analysis",
                "url": f"https://www.deloitte.com/{industry}-market-intelligence",
                "source": "Deloitte",
                "reliability": 0.85,
                "date": "2024-07-08",
                "content_type": "analysis"
            }
        ])
        
        return mock_sources[:self.max_sources]
    
    def _process_search_results(self, llm_response: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa risultati di ricerca in formato strutturato"""
        findings = {
            "sources": search_results,
            "findings": {
                "market_overview": self._extract_section(llm_response, "market overview"),
                "industry_analysis": self._extract_section(llm_response, "industry analysis"),
                "trends_developments": self._extract_section(llm_response, "trends"),
                "strategic_insights": self._extract_section(llm_response, "strategic insights"),
                "expert_perspectives": self._extract_section(llm_response, "expert perspectives")
            },
            "key_statistics": self._extract_statistics(llm_response),
            "recent_developments": self._extract_recent_developments(llm_response)
        }
        
        return findings
    
    def _extract_section(self, text: str, section_keyword: str) -> str:
        """Estrae sezione specifica dal testo"""
        # Cerca pattern per identificare sezioni
        lines = text.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            if section_keyword.lower() in line.lower() and ('**' in line or '#' in line):
                in_section = True
                continue
            elif in_section and ('**' in line or '#' in line) and section_keyword.lower() not in line.lower():
                break
            elif in_section:
                section_content.append(line.strip())
        
        return '\n'.join(section_content).strip() if section_content else f"Information about {section_keyword} from comprehensive research analysis."
    
    def _extract_statistics(self, text: str) -> List[Dict[str, Any]]:
        """Estrae statistiche e numeri chiave dal testo"""
        statistics = []
        
        # Pattern per trovare statistiche con contesto
        stat_patterns = [
            r"(\$[\d,]+\.?\d*\s*(?:billion|million|trillion))",  # Valori monetari
            r"(\d+\.?\d*%)",  # Percentuali
            r"(\d+\.?\d*\s*(?:billion|million|thousand))",  # Numeri grandi
        ]
        
        for pattern in stat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Cerca contesto intorno al numero
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                statistics.append({
                    "value": match.group(1),
                    "context": context,
                    "position": match.start()
                })
        
        return statistics[:10]  # Limita a 10 statistiche più rilevanti
    
    def _extract_recent_developments(self, text: str) -> List[str]:
        """Estrae sviluppi recenti dal testo"""
        developments = []
        
        # Cerca frasi che indicano sviluppi recenti
        recent_indicators = [
            "recently", "latest", "new", "announced", "launched", "acquired", 
            "merged", "partnership", "investment", "funding"
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in recent_indicators):
                if len(sentence.strip()) > 20:  # Filtra frasi troppo corte
                    developments.append(sentence.strip())
        
        return developments[:5]
    
    async def _extract_insights(self, findings: Dict[str, Any], query: str) -> List[str]:
        """Estrae insights qualitativi dai findings"""
        insights = []
        
        # Insights dalle fonti
        sources = findings.get("sources", [])
        if sources:
            high_reliability_sources = [s for s in sources if s.get("reliability", 0) > 0.85]
            insights.append(f"Analysis based on {len(sources)} sources, {len(high_reliability_sources)} high-reliability")
        
        # Insights dalle statistiche
        statistics = findings.get("key_statistics", [])
        if statistics:
            insights.append(f"Found {len(statistics)} key statistical data points")
            # Aggiungi insight specifico dalla prima statistica
            if statistics:
                first_stat = statistics[0]
                insights.append(f"Key metric identified: {first_stat['value']} - {first_stat['context'][:100]}...")
        
        # Insights dai recent developments
        developments = findings.get("recent_developments", [])
        if developments:
            insights.append(f"Identified {len(developments)} recent market developments")
            insights.append(f"Latest development: {developments[0][:150]}...")
        
        # Insights specifici per tipo di query
        if "fintech" in query.lower():
            insights.extend([
                "Fintech sector showing strong digital transformation momentum",
                "Regulatory compliance and security remain key focus areas",
                "Investment patterns indicate growing institutional adoption"
            ])
        
        if "market" in query.lower():
            insights.extend([
                "Market consolidation trends visible across major players",
                "Customer acquisition costs and retention metrics are key performance indicators"
            ])
        
        return insights[:8]
    
    def _calculate_reliability_score(self, findings: Dict[str, Any]) -> float:
        """Calcola score di affidabilità delle fonti"""
        sources = findings.get("sources", [])
        if not sources:
            return 0.5
        
        # Media ponderata dell'affidabilità delle fonti
        total_reliability = sum(source.get("reliability", 0.5) for source in sources)
        avg_reliability = total_reliability / len(sources)
        
        # Bonus per diversità delle fonti
        source_types = set(source.get("source", "unknown") for source in sources)
        diversity_bonus = min(0.1, len(source_types) * 0.02)
        
        # Penalty per fonti datate (simulato)
        recency_score = 0.9  # Mock recency score
        
        final_score = (avg_reliability + diversity_bonus) * recency_score
        return min(final_score, 1.0)
    
    def _create_search_summary(self, findings: Dict[str, Any], query: str) -> str:
        """Crea summary del processo di ricerca"""
        sources_count = len(findings.get("sources", []))
        statistics_count = len(findings.get("key_statistics", []))
        developments_count = len(findings.get("recent_developments", []))
        
        summary = f"""
        Research Summary for: {query}
        
        - Sources Analyzed: {sources_count}
        - Key Statistics Found: {statistics_count}
        - Recent Developments: {developments_count}
        - Research Depth: Comprehensive multi-source analysis
        - Coverage: Market overview, competitive landscape, trends, strategic insights
        
        The research provides actionable intelligence for strategic decision-making
        with focus on current market dynamics and future growth opportunities.
        """
        
        return summary.strip()
    
    def _generate_research_recommendations(self, insights: List[str], query: str) -> List[str]:
        """Genera raccomandazioni basate sulla ricerca"""
        recommendations = [
            "Continue monitoring market developments for strategic opportunities",
            "Validate findings with primary research and expert interviews",
            "Track key metrics and KPIs identified in the analysis regularly"
        ]
        
        # Raccomandazioni specifiche per tipo di ricerca
        if "competitive" in query.lower():
            recommendations.extend([
                "Conduct deep-dive analysis on top 3 competitors",
                "Benchmark positioning against market leaders"
            ])
        
        if "trend" in query.lower():
            recommendations.extend([
                "Develop strategic response to identified market trends",
                "Monitor early indicators of emerging opportunities"
            ])
        
        if "fintech" in query.lower():
            recommendations.extend([
                "Assess regulatory compliance requirements in target markets",
                "Evaluate partnership opportunities with established financial institutions"
            ])
        
        return recommendations[:5]
