"""
Data Analyst Agent

Agente specializzato nell'elaborazione di dati numerici, calcolo di KPI,
analisi statistiche e generazione di insights quantitativi.
"""

from typing import Dict, Any, Optional, List
import json
import re
from .base_agent import BaseAgent, AgentType, AgentStatus
import pandas as pd
import numpy as np
from loguru import logger


class DataAnalystAgent(BaseAgent):
    """
    Agente AI specializzato in analisi dati e statistiche
    """
    
    def __init__(self, memory_manager=None):
        """
        Inizializza il Data Analyst Agent
        """
        super().__init__(AgentType.DATA_ANALYST, memory_manager)
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa richieste di analisi dati
        
        Args:
            query: Query che richiede analisi numerica/statistica
            context: Contesto con eventuali dati da analizzare
            
        Returns:
            Dizionario con analisi dati e KPI
        """
        self._update_status(AgentStatus.RUNNING)
        
        try:
            # Analizza la query per estrarre requisiti di analisi
            analysis_requirements = self._parse_analysis_requirements(query)
            
            # Genera prompt per l'LLM
            system_prompt = self.get_system_prompt()
            user_prompt = self._create_analysis_prompt(query, analysis_requirements, context)
            
            # Chiama LLM per analisi
            llm_response = await self._call_llm(user_prompt, system_prompt)
            
            # Processa la risposta e genera struttura dati
            analysis_result = self._process_llm_response(llm_response, query)
            
            # Calcola KPI addizionali se possibile
            kpis = await self._calculate_kpis(analysis_result, query)
            
            # Genera insights quantitativi
            insights = await self._generate_insights(analysis_result, kpis, query)
            
            result = {
                "agent": self.agent_type.value,
                "status": "completed",
                "query": query,
                "analysis": analysis_result,
                "kpis": kpis,
                "insights": insights,
                "data_quality_score": self._assess_data_quality(analysis_result),
                "confidence_score": 0.85,  # Mock confidence score
                "recommendations": self._generate_recommendations(analysis_result, insights)
            }
            
            self._update_status(AgentStatus.COMPLETED)
            return result
            
        except Exception as e:
            self._update_status(AgentStatus.ERROR)
            logger.error(f"Error in DataAnalystAgent: {e}")
            return {
                "agent": self.agent_type.value,
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    def get_system_prompt(self) -> str:
        """System prompt ottimizzato per analisi dati"""
        return """
        You are an expert Data Analyst AI specialized in:
        
        - Comprehensive statistical analysis of datasets and market data
        - Calculation and interpretation of business KPIs and metrics
        - Identification of trends, patterns, and anomalies in data
        - Generation of quantitative insights and actionable intelligence
        - Data quality assessment and validation
        
        When analyzing data or responding to analytical queries:
        1. Provide detailed statistical analysis with specific numbers and metrics
        2. Calculate relevant KPIs for the specific domain or industry
        3. Identify significant trends, patterns, and outliers
        4. Generate practical, data-driven insights
        5. Assess data reliability and highlight any limitations
        
        Always structure your response in a clear, analytical format with:
        - Key statistics and metrics
        - Trend analysis
        - Performance indicators
        - Data-driven insights
        - Actionable recommendations based on the analysis
        
        Be specific with numbers, percentages, and quantitative measures wherever possible.
        """
    
    def _parse_analysis_requirements(self, query: str) -> Dict[str, Any]:
        """Analizza la query per identificare requisiti di analisi"""
        requirements = {
            "metrics_requested": [],
            "time_period": None,
            "geographic_scope": None,
            "industry": None,
            "analysis_type": "general"
        }
        
        # Cerca metriche specifiche
        metrics_patterns = [
            r"revenue", r"growth", r"market share", r"roi", r"conversion",
            r"kpi", r"performance", r"statistics", r"trends", r"analysis"
        ]
        
        for pattern in metrics_patterns:
            if re.search(pattern, query.lower()):
                requirements["metrics_requested"].append(pattern)
        
        # Cerca indicatori temporali
        time_patterns = [
            r"2024", r"2023", r"quarterly", r"monthly", r"yearly", r"annual"
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, query.lower()):
                requirements["time_period"] = pattern
                break
        
        # Cerca scope geografico
        geo_patterns = [
            r"europe", r"usa", r"global", r"international", r"domestic"
        ]
        
        for pattern in geo_patterns:
            if re.search(pattern, query.lower()):
                requirements["geographic_scope"] = pattern
                break
        
        # Identifica industry/settore
        industry_patterns = [
            r"fintech", r"technology", r"healthcare", r"finance", r"retail", r"manufacturing"
        ]
        
        for pattern in industry_patterns:
            if re.search(pattern, query.lower()):
                requirements["industry"] = pattern
                break
        
        return requirements
    
    def _create_analysis_prompt(self, query: str, requirements: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Crea il prompt per l'analisi LLM"""
        prompt = f"""
        Analyze the following request and provide detailed quantitative analysis:
        
        Query: {query}
        
        Analysis Requirements:
        - Metrics Focus: {', '.join(requirements.get('metrics_requested', ['general']))}
        - Time Period: {requirements.get('time_period', 'current')}
        - Geographic Scope: {requirements.get('geographic_scope', 'not specified')}
        - Industry: {requirements.get('industry', 'general')}
        
        Please provide:
        1. Key statistics and numerical data points
        2. Performance metrics and KPIs
        3. Trend analysis with specific percentages/growth rates
        4. Market size estimates where applicable
        5. Comparative analysis (year-over-year, competitor benchmarks)
        6. Risk factors and data limitations
        
        Format your response as structured analytical content with clear sections and specific numerical data.
        """
        
        if context:
            prompt += f"\n\nAdditional Context: {json.dumps(context, indent=2)}"
        
        return prompt
    
    def _process_llm_response(self, llm_response: str, query: str) -> Dict[str, Any]:
        """Processa la risposta LLM in formato strutturato"""
        # Estrae numeri e metriche dalla risposta
        numbers = re.findall(r'\d+\.?\d*%?', llm_response)
        
        # Struttura base dell'analisi
        analysis = {
            "raw_response": llm_response,
            "extracted_metrics": numbers[:10],  # Prime 10 metriche trovate
            "key_findings": self._extract_key_findings(llm_response),
            "statistical_summary": self._create_statistical_summary(llm_response),
            "trend_indicators": self._extract_trend_indicators(llm_response)
        }
        
        return analysis
    
    def _extract_key_findings(self, response: str) -> List[str]:
        """Estrae key findings dalla risposta"""
        # Cerca frasi che indicano findings importanti
        sentences = response.split('.')
        key_findings = []
        
        keywords = ['growth', 'increase', 'decrease', 'trend', 'significant', 'major', 'key']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                key_findings.append(sentence.strip())
        
        return key_findings[:5]  # Top 5 findings
    
    def _create_statistical_summary(self, response: str) -> Dict[str, Any]:
        """Crea summary statistico"""
        # Estrae numeri per creare summary basic
        numbers = [float(match.replace('%', '')) for match in re.findall(r'\d+\.?\d*', response)]
        
        if numbers:
            return {
                "total_metrics_found": len(numbers),
                "average_value": np.mean(numbers),
                "max_value": max(numbers),
                "min_value": min(numbers),
                "std_deviation": np.std(numbers) if len(numbers) > 1 else 0
            }
        
        return {"total_metrics_found": 0}
    
    def _extract_trend_indicators(self, response: str) -> List[str]:
        """Estrae indicatori di trend"""
        trends = []
        trend_words = ['growing', 'declining', 'stable', 'increasing', 'decreasing', 'rising', 'falling']
        
        for word in trend_words:
            if word in response.lower():
                trends.append(word)
        
        return list(set(trends))  # Rimuove duplicati
    
    async def _calculate_kpis(self, analysis_result: Dict[str, Any], query: str) -> Dict[str, float]:
        """Calcola KPI specifici basati sui dati"""
        kpis = {}
        
        # KPI simulati basati su query type
        if "market" in query.lower():
            kpis.update({
                "market_growth_rate": 12.5,
                "market_penetration": 35.7,
                "competitive_index": 0.68
            })
        
        if "fintech" in query.lower():
            kpis.update({
                "adoption_rate": 28.3,
                "transaction_volume_growth": 45.2,
                "user_acquisition_cost": 125.0
            })
        
        if "revenue" in query.lower():
            kpis.update({
                "revenue_growth_yoy": 18.4,
                "profit_margin": 15.2,
                "roi": 22.8
            })
        
        # Aggiunge KPI generici
        kpis.update({
            "confidence_score": 0.85,
            "data_completeness": 0.92,
            "analysis_depth_score": 0.78
        })
        
        return kpis
    
    async def _generate_insights(self, analysis_result: Dict[str, Any], kpis: Dict[str, float], query: str) -> List[str]:
        """Genera insights quantitativi"""
        insights = []
        
        # Insights basati sui KPI
        for kpi_name, value in kpis.items():
            if "growth" in kpi_name and value > 10:
                insights.append(f"Strong growth indicated by {kpi_name}: {value}%")
            elif "score" in kpi_name and value > 0.8:
                insights.append(f"High performance in {kpi_name}: {value:.2f}")
        
        # Insights dalle key findings
        if analysis_result.get("key_findings"):
            insights.extend([
                f"Key finding: {finding}" for finding in analysis_result["key_findings"][:3]
            ])
        
        # Trend insights
        trends = analysis_result.get("trend_indicators", [])
        if trends:
            insights.append(f"Market trends showing: {', '.join(trends)}")
        
        return insights[:8]  # Limita a 8 insights
    
    def _assess_data_quality(self, analysis_result: Dict[str, Any]) -> float:
        """Valuta la qualità dei dati analizzati"""
        # Score basato su completezza e presenza di metriche
        score = 0.5  # Base score
        
        if analysis_result.get("extracted_metrics"):
            score += 0.2
        
        if analysis_result.get("key_findings"):
            score += 0.15
        
        if analysis_result.get("statistical_summary", {}).get("total_metrics_found", 0) > 3:
            score += 0.15
        
        return min(score, 1.0)
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any], insights: List[str]) -> List[str]:
        """Genera raccomandazioni basate sull'analisi"""
        recommendations = []
        
        # Raccomandazioni standard
        recommendations.extend([
            "Monitor key performance metrics regularly for trend detection",
            "Conduct deeper analysis on identified growth opportunities",
            "Validate findings with additional data sources when possible"
        ])
        
        # Raccomandazioni specifiche basate sui trends
        trends = analysis_result.get("trend_indicators", [])
        if "growing" in trends:
            recommendations.append("Capitalize on growth trends with strategic investments")
        if "declining" in trends:
            recommendations.append("Investigate decline causes and implement corrective measures")
        
        return recommendations[:5]
