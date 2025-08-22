"""
Copywriter Agent

Agente specializzato nella creazione di report narrativi finali,
sintesi degli output degli altri agenti in formato leggibile e professionale.
"""

from typing import Dict, Any, Optional, List
import re
import json
from .base_agent import BaseAgent, AgentType, AgentStatus
from loguru import logger


class CopywriterAgent(BaseAgent):
    """
    Agente AI specializzato in copywriting e generazione report
    """
    
    def __init__(self, memory_manager=None):
        """
        Inizializza il Copywriter Agent
        """
        super().__init__(AgentType.COPYWRITER, memory_manager)
        self.default_tone = "professional"
        self.report_templates = {
            "business_report": "comprehensive",
            "executive_summary": "concise",
            "market_analysis": "analytical"
        }
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa output degli altri agenti per creare report finale
        
        Args:
            query: Query originale dell'utente
            context: Context con output di Data Analyst e Researcher
            
        Returns:
            Dizionario con report narrativo finale e componenti
        """
        self._update_status(AgentStatus.RUNNING)
        
        try:
            # Estrai output dagli altri agenti
            agent_outputs = self._extract_agent_outputs(context)
            
            # Analizza il tono e stile richiesto
            writing_style = self._determine_writing_style(query, context)
            
            # Crea struttura narrativa
            narrative_structure = await self._create_narrative_structure(agent_outputs, query)
            
            # Genera le sezioni del report
            executive_summary = await self._generate_executive_summary(agent_outputs, query)
            key_findings = await self._extract_key_findings(agent_outputs)
            recommendations = await self._generate_recommendations(agent_outputs, query)
            
            # Genera report finale
            final_report = await self._generate_final_report(
                narrative_structure, executive_summary, key_findings, recommendations, writing_style
            )
            
            # Calcola metriche del report
            report_metrics = self._calculate_reading_metrics(final_report)
            
            result = {
                "agent": self.agent_type.value,
                "status": "completed",
                "query": query,
                "final_report": final_report,
                "executive_summary": executive_summary,
                "key_findings": key_findings,
                "recommendations": recommendations,
                "narrative_structure": narrative_structure,
                "report_metadata": {
                    **report_metrics,
                    "tone": writing_style["tone"],
                    "format": writing_style["format"],
                    "target_audience": writing_style["audience"]
                },
                "sources_integrated": len(agent_outputs.get("data_analyst", {}).get("kpis", {})) + len(agent_outputs.get("researcher", {}).get("sources", []))
            }
            
            self._update_status(AgentStatus.COMPLETED)
            return result
            
        except Exception as e:
            self._update_status(AgentStatus.ERROR)
            logger.error(f"Error in CopywriterAgent: {e}")
            return {
                "agent": self.agent_type.value,
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    def get_system_prompt(self) -> str:
        """System prompt ottimizzato per copywriting"""
        return """
        You are an expert Business Copywriter AI specialized in:
        
        - Creating professional, engaging business reports and analyses
        - Synthesizing complex information into clear, compelling narratives
        - Adapting tone of voice and style to target audiences
        - Generating impactful executive summaries and key findings
        - Formulating actionable recommendations based on data and research
        
        When creating reports:
        1. Start with a compelling executive summary that captures the essence
        2. Structure content with logical flow and persuasive narrative
        3. Balance quantitative data with qualitative insights effectively
        4. Use clear headings, formatting, and structure for readability
        5. Always conclude with specific, actionable recommendations
        
        Writing Style Guidelines:
        - Professional but accessible tone
        - Clear, concise language avoiding unnecessary jargon
        - Data-driven insights supported by evidence
        - Strategic perspective with business implications
        - Action-oriented conclusions and next steps
        
        Create comprehensive, well-structured reports that inform decision-making
        and provide clear strategic direction based on the analysis provided.
        """
    
    def _extract_agent_outputs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae gli output degli altri agenti dal contesto"""
        agent_outputs = {
            "data_analyst": {},
            "researcher": {}
        }
        
        if context:
            # Cerca output del data analyst
            for key, value in context.items():
                if "agent_output:data_analyst" in str(key) or "data_analyst" in str(key):
                    agent_outputs["data_analyst"] = value
                elif "agent_output:researcher" in str(key) or "researcher" in str(key):
                    agent_outputs["researcher"] = value
        
        return agent_outputs
    
    def _determine_writing_style(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determina il tono e stile di scrittura appropriato"""
        style = {
            "tone": "professional",
            "format": "business_report",
            "audience": "business_stakeholders",
            "formality": "formal",
            "technical_level": "moderate"
        }
        
        # Analizza la query per adattare lo stile
        if re.search(r"executive|board|leadership|c-level", query.lower()):
            style.update({
                "tone": "executive",
                "format": "executive_summary",
                "audience": "senior_management",
                "formality": "high"
            })
        
        if re.search(r"technical|analysis|detailed|comprehensive", query.lower()):
            style.update({
                "technical_level": "high",
                "format": "detailed_analysis"
            })
        
        if re.search(r"summary|brief|overview", query.lower()):
            style.update({
                "format": "summary_report",
                "technical_level": "low"
            })
        
        return style
    
    async def _create_narrative_structure(self, agent_outputs: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Crea la struttura narrativa del report"""
        
        # Analizza il contenuto disponibile
        has_data_analysis = bool(agent_outputs.get("data_analyst"))
        has_research = bool(agent_outputs.get("researcher"))
        
        structure = {
            "introduction": {
                "purpose": f"Analysis of {query}",
                "scope": "Comprehensive multi-agent analysis",
                "methodology": []
            },
            "sections": [],
            "conclusion": {
                "summary": True,
                "recommendations": True,
                "next_steps": True
            }
        }
        
        # Aggiungi metodologia basata sugli agenti utilizzati
        if has_data_analysis:
            structure["introduction"]["methodology"].append("Quantitative data analysis and KPI evaluation")
        if has_research:
            structure["introduction"]["methodology"].append("Comprehensive market research and trend analysis")
        
        # Definisci sezioni in base al contenuto disponibile
        if has_data_analysis and has_research:
            structure["sections"] = [
                {"title": "Executive Summary", "type": "summary"},
                {"title": "Market Overview & Context", "type": "research_findings"},
                {"title": "Data Analysis & Key Metrics", "type": "data_analysis"},
                {"title": "Strategic Insights & Trends", "type": "combined_insights"},
                {"title": "Recommendations & Next Steps", "type": "recommendations"}
            ]
        elif has_data_analysis:
            structure["sections"] = [
                {"title": "Executive Summary", "type": "summary"},
                {"title": "Data Analysis & KPIs", "type": "data_analysis"},
                {"title": "Key Insights", "type": "insights"},
                {"title": "Recommendations", "type": "recommendations"}
            ]
        elif has_research:
            structure["sections"] = [
                {"title": "Executive Summary", "type": "summary"},
                {"title": "Research Findings", "type": "research_findings"},
                {"title": "Market Insights", "type": "insights"},
                {"title": "Strategic Recommendations", "type": "recommendations"}
            ]
        
        return structure
    
    async def _generate_executive_summary(self, agent_outputs: Dict[str, Any], query: str) -> str:
        """Genera executive summary del report"""
        
        # Costruisci prompt per l'executive summary
        summary_prompt = f"""
        Create a compelling executive summary for the following business analysis:
        
        Analysis Topic: {query}
        
        Available Insights:
        """
        
        # Aggiungi insights dal data analyst
        data_insights = agent_outputs.get("data_analyst", {}).get("insights", [])
        if data_insights:
            summary_prompt += f"\n\nKey Data Insights:\n" + "\n".join(f"- {insight}" for insight in data_insights[:5])
        
        # Aggiungi insights dal researcher
        research_insights = agent_outputs.get("researcher", {}).get("insights", [])
        if research_insights:
            summary_prompt += f"\n\nMarket Research Insights:\n" + "\n".join(f"- {insight}" for insight in research_insights[:5])
        
        # Aggiungi KPI se disponibili
        kpis = agent_outputs.get("data_analyst", {}).get("kpis", {})
        if kpis:
            summary_prompt += f"\n\nKey Performance Indicators:\n"
            for kpi_name, kpi_value in list(kpis.items())[:5]:
                summary_prompt += f"- {kpi_name}: {kpi_value}\n"
        
        summary_prompt += """
        
        Create a concise but comprehensive executive summary (200-300 words) that:
        1. Clearly states the purpose and scope of the analysis
        2. Highlights the most critical findings and insights
        3. Presents key metrics and performance indicators
        4. Outlines the strategic implications
        5. Sets up the detailed analysis that follows
        
        Write in a professional, executive-level tone suitable for senior decision-makers.
        """
        
        system_prompt = "You are an expert business analyst creating executive summaries for senior leadership."
        
        return await self._call_llm(summary_prompt, system_prompt)
    
    async def _extract_key_findings(self, agent_outputs: Dict[str, Any]) -> List[str]:
        """Estrae e prioritizza i key findings"""
        key_findings = []
        
        # Findings dal data analyst
        data_analysis = agent_outputs.get("data_analyst", {})
        if data_analysis:
            # KPI highlights
            kpis = data_analysis.get("kpis", {})
            for kpi_name, kpi_value in list(kpis.items())[:3]:
                key_findings.append(f"**{kpi_name.replace('_', ' ').title()}**: {kpi_value}")
            
            # Data insights
            data_insights = data_analysis.get("insights", [])
            key_findings.extend([f"📊 {insight}" for insight in data_insights[:3]])
        
        # Findings dal researcher
        research_data = agent_outputs.get("researcher", {})
        if research_data:
            # Research insights
            research_insights = research_data.get("insights", [])
            key_findings.extend([f"🔍 {insight}" for insight in research_insights[:3]])
            
            # Recent developments
            developments = research_data.get("recent_developments", [])
            if developments:
                key_findings.append(f"📈 Recent Development: {developments[0][:150]}...")
        
        # Filtra e prioritizza
        return key_findings[:8]
    
    async def _generate_recommendations(self, agent_outputs: Dict[str, Any], query: str) -> List[str]:
        """Genera raccomandazioni actionable basate sui findings"""
        
        recommendations_prompt = f"""
        Based on the comprehensive analysis conducted, generate strategic recommendations for:
        
        Analysis Topic: {query}
        
        Analysis Results Summary:
        """
        
        # Includi dati chiave per le raccomandazioni
        data_analysis = agent_outputs.get("data_analyst", {})
        if data_analysis:
            recommendations_prompt += f"\nData Analysis Results: {json.dumps(data_analysis.get('insights', [])[:3])}"
        
        research_data = agent_outputs.get("researcher", {})
        if research_data:
            recommendations_prompt += f"\nResearch Findings: {json.dumps(research_data.get('insights', [])[:3])}"
        
        recommendations_prompt += """
        
        Generate 5-7 specific, actionable strategic recommendations that:
        1. Are directly based on the analysis findings
        2. Address key opportunities and challenges identified
        3. Provide clear next steps and action items
        4. Consider both short-term and long-term implications
        5. Are realistic and implementable
        
        Format each recommendation as a clear, actionable statement with brief justification.
        """
        
        system_prompt = "You are a strategic business consultant providing actionable recommendations based on comprehensive analysis."
        
        recommendations_text = await self._call_llm(recommendations_prompt, system_prompt)
        
        # Parse recommendations into list
        recommendations = []
        lines = recommendations_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or re.match(r'\d+\.', line)):
                recommendations.append(line)
        
        return recommendations[:7]
    
    async def _generate_final_report(self, narrative_structure: Dict[str, Any], 
                                   executive_summary: str, key_findings: List[str], 
                                   recommendations: List[str], writing_style: Dict[str, Any]) -> str:
        """Genera il report finale completo"""
        
        report_prompt = f"""
        Create a comprehensive business report with the following structure and content:
        
        REPORT STRUCTURE:
        {json.dumps(narrative_structure, indent=2)}
        
        CONTENT COMPONENTS:
        
        Executive Summary:
        {executive_summary}
        
        Key Findings:
        {chr(10).join(key_findings)}
        
        Strategic Recommendations:
        {chr(10).join(recommendations)}
        
        WRITING REQUIREMENTS:
        - Tone: {writing_style['tone']}
        - Format: {writing_style['format']}
        - Audience: {writing_style['audience']}
        - Technical Level: {writing_style['technical_level']}
        
        Create a complete, professional business report (1000-1500 words) that:
        1. Flows logically from introduction through analysis to conclusions
        2. Integrates all provided content seamlessly
        3. Uses appropriate business language and formatting
        4. Includes clear section headers and structure
        5. Maintains consistent tone throughout
        6. Provides strategic value for decision-making
        
        Format with clear sections, headers, and professional business report structure.
        """
        
        system_prompt = self.get_system_prompt()
        
        return await self._call_llm(report_prompt, system_prompt)
    
    def _calculate_reading_metrics(self, text: str) -> Dict[str, int]:
        """Calcola metriche del testo (word count, reading time, etc.)"""
        if not text:
            return {"word_count": 0, "reading_time_minutes": 0, "paragraph_count": 0}
        
        # Conta parole
        words = len(text.split())
        
        # Stima tempo di lettura (200 parole per minuto)
        reading_time = max(1, words // 200)
        
        # Conta paragrafi
        paragraphs = len([p for p in text.split('\n\n') if p.strip()])
        
        # Conta sezioni (headers con #)
        sections = len(re.findall(r'^#+\s+', text, re.MULTILINE))
        
        return {
            "word_count": words,
            "reading_time_minutes": reading_time,
            "paragraph_count": paragraphs,
            "section_count": sections,
            "character_count": len(text),
            "readability_score": self._calculate_readability_score(text)
        }
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calcola un semplice score di leggibilità"""
        if not text:
            return 0.0
        
        sentences = text.count('.') + text.count('!') + text.count('?')
        words = len(text.split())
        
        if sentences == 0:
            return 0.5
        
        avg_words_per_sentence = words / sentences
        
        # Score basato su lunghezza media delle frasi (più basso = più leggibile)
        if avg_words_per_sentence < 15:
            return 0.9  # Molto leggibile
        elif avg_words_per_sentence < 20:
            return 0.7  # Buona leggibilità
        elif avg_words_per_sentence < 25:
            return 0.5  # Media leggibilità
        else:
            return 0.3  # Difficile da leggere
