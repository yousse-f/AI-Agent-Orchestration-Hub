"""
Orchestrator Centrale

Coordina l'esecuzione degli agenti specializzati (Data Analyst, Researcher, Copywriter).
Gestisce il flusso di lavoro, la sequenza di esecuzione e l'aggregazione dei risultati.
"""

from typing import Dict, List, Any
from enum import Enum
import uuid
import asyncio
from loguru import logger

from .memory import MemoryManager
from .agents.data_analyst import DataAnalystAgent
from .agents.researcher import ResearcherAgent
from .agents.copywriter import CopywriterAgent


class ExecutionMode(Enum):
    """Modi di esecuzione degli agenti"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DYNAMIC = "dynamic"


class Orchestrator:
    """
    Orchestratore centrale per il coordinamento degli agenti AI
    """
    
    def __init__(self, redis_url: str = None):
        """
        Inizializza l'orchestratore con configurazione e agenti
        """
        # Inizializza memory manager
        self.memory_manager = MemoryManager(redis_url)
        
        # Inizializza agenti
        self.data_analyst = DataAnalystAgent(self.memory_manager)
        self.researcher = ResearcherAgent(self.memory_manager)
        self.copywriter = CopywriterAgent(self.memory_manager)
        
        # Configurazione esecuzione
        self.default_execution_mode = ExecutionMode.SEQUENTIAL
        self.agent_timeout = 300  # 5 minutes per agent
        
        logger.info("Orchestrator initialized with all agents")
    
    async def process_request(self, query: str, execution_mode: ExecutionMode = None) -> Dict[str, Any]:
        """
        Processa una richiesta utente coordinando gli agenti
        
        Args:
            query: Query dell'utente da processare
            execution_mode: Modalità di esecuzione degli agenti
            
        Returns:
            Dizionario con risultati di tutti gli agenti e report finale
        """
        session_id = str(uuid.uuid4())
        execution_mode = execution_mode or self._determine_execution_strategy(query)
        
        logger.info(f"Processing request with session {session_id}, mode: {execution_mode.value}")
        
        try:
            # Memorizza la query iniziale
            await self.memory_manager.store_context(session_id, "original_query", query)
            await self.memory_manager.store_context(session_id, "execution_mode", execution_mode.value)
            
            # Esegui agenti in base alla strategia
            if execution_mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential(query, session_id)
            elif execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel(query, session_id)
            else:  # DYNAMIC
                results = await self._execute_dynamic(query, session_id)
            
            # Aggrega i risultati finali
            final_result = await self._aggregate_results(results, query, session_id)
            
            logger.info(f"Successfully processed request for session {session_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
                "query": query
            }
    
    def _determine_execution_strategy(self, query: str) -> ExecutionMode:
        """
        Determina la strategia di esecuzione ottimale basata sulla query
        """
        # Analisi semplice della query per determinare la strategia
        query_lower = query.lower()
        
        # Se richiede analisi rapida o summary, usa parallel
        if any(keyword in query_lower for keyword in ["quick", "summary", "brief", "overview"]):
            return ExecutionMode.PARALLEL
        
        # Se richiede analisi approfondita, usa sequential per migliore qualità
        if any(keyword in query_lower for keyword in ["detailed", "comprehensive", "thorough", "deep"]):
            return ExecutionMode.SEQUENTIAL
        
        # Default: sequential per migliore coerenza
        return ExecutionMode.SEQUENTIAL
    
    async def _execute_sequential(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Esecuzione sequenziale: DataAnalyst → Researcher → Copywriter
        """
        logger.info(f"Starting sequential execution for session {session_id}")
        results = {}
        
        try:
            # 1. Data Analyst
            logger.info("Running Data Analyst...")
            data_analyst_result = await asyncio.wait_for(
                self.data_analyst.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["data_analyst"] = data_analyst_result
            
            # 2. Researcher (con contesto del Data Analyst)
            logger.info("Running Researcher...")
            researcher_result = await asyncio.wait_for(
                self.researcher.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["researcher"] = researcher_result
            
            # 3. Copywriter (con contesto di entrambi gli agenti precedenti)
            logger.info("Running Copywriter...")
            copywriter_result = await asyncio.wait_for(
                self.copywriter.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["copywriter"] = copywriter_result
            
            results["execution_mode"] = "sequential"
            results["execution_order"] = ["data_analyst", "researcher", "copywriter"]
            
            return results
            
        except asyncio.TimeoutError:
            logger.error("Timeout during sequential execution")
            results["error"] = "Agent execution timeout"
            return results
        except Exception as e:
            logger.error(f"Error in sequential execution: {e}")
            results["error"] = str(e)
            return results
    
    async def _execute_parallel(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Esecuzione parallela: DataAnalyst e Researcher in parallelo → Copywriter
        """
        logger.info(f"Starting parallel execution for session {session_id}")
        results = {}
        
        try:
            # Fase 1: Esegui Data Analyst e Researcher in parallelo
            logger.info("Running Data Analyst and Researcher in parallel...")
            
            parallel_tasks = [
                asyncio.wait_for(self.data_analyst.run(query, session_id), timeout=self.agent_timeout),
                asyncio.wait_for(self.researcher.run(query, session_id), timeout=self.agent_timeout)
            ]
            
            data_analyst_result, researcher_result = await asyncio.gather(*parallel_tasks)
            
            results["data_analyst"] = data_analyst_result
            results["researcher"] = researcher_result
            
            # Fase 2: Esegui Copywriter con tutti i risultati disponibili
            logger.info("Running Copywriter with parallel results...")
            
            copywriter_result = await asyncio.wait_for(
                self.copywriter.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["copywriter"] = copywriter_result
            
            results["execution_mode"] = "parallel"
            results["execution_phases"] = [
                ["data_analyst", "researcher"],
                ["copywriter"]
            ]
            
            return results
            
        except asyncio.TimeoutError:
            logger.error("Timeout during parallel execution")
            results["error"] = "Agent execution timeout"
            return results
        except Exception as e:
            logger.error(f"Error in parallel execution: {e}")
            results["error"] = str(e)
            return results
    
    async def _execute_dynamic(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Esecuzione dinamica: determina l'ordine ottimale in base alla query
        """
        logger.info(f"Starting dynamic execution for session {session_id}")
        
        # Per ora, usa logica semplice per determinare l'approccio
        query_lower = query.lower()
        
        # Se la query è principalmente quantitativa, inizia con Data Analyst
        if any(keyword in query_lower for keyword in ["data", "statistics", "numbers", "kpi", "metrics"]):
            return await self._execute_sequential(query, session_id)
        
        # Se la query è principalmente qualitativa, inizia con Researcher
        elif any(keyword in query_lower for keyword in ["market", "trends", "research", "analysis", "industry"]):
            return await self._execute_research_first(query, session_id)
        
        # Default: esecuzione parallela per bilanciare velocità e qualità
        else:
            return await self._execute_parallel(query, session_id)
    
    async def _execute_research_first(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Variante dinamica: Researcher → DataAnalyst → Copywriter
        """
        logger.info(f"Starting research-first execution for session {session_id}")
        results = {}
        
        try:
            # 1. Researcher per stabilire contesto
            logger.info("Running Researcher first...")
            researcher_result = await asyncio.wait_for(
                self.researcher.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["researcher"] = researcher_result
            
            # 2. Data Analyst con contesto di ricerca
            logger.info("Running Data Analyst with research context...")
            data_analyst_result = await asyncio.wait_for(
                self.data_analyst.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["data_analyst"] = data_analyst_result
            
            # 3. Copywriter con tutto il contesto
            logger.info("Running Copywriter...")
            copywriter_result = await asyncio.wait_for(
                self.copywriter.run(query, session_id),
                timeout=self.agent_timeout
            )
            results["copywriter"] = copywriter_result
            
            results["execution_mode"] = "dynamic_research_first"
            results["execution_order"] = ["researcher", "data_analyst", "copywriter"]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in research-first execution: {e}")
            results["error"] = str(e)
            return results
    
    async def _aggregate_results(self, results: Dict[str, Any], original_query: str, session_id: str) -> Dict[str, Any]:
        """
        Aggrega i risultati di tutti gli agenti in un formato finale strutturato
        """
        logger.info(f"Aggregating results for session {session_id}")
        
        # Estrai risultati principali
        data_analyst_result = results.get("data_analyst", {})
        researcher_result = results.get("researcher", {})
        copywriter_result = results.get("copywriter", {})
        
        # Determina lo stato globale
        global_status = "completed"
        if results.get("error") or any(result.get("status") == "error" for result in results.values() if isinstance(result, dict)):
            global_status = "error"
        elif any(result.get("status") == "running" for result in results.values() if isinstance(result, dict)):
            global_status = "running"
        
        # Aggrega insights da tutti gli agenti
        all_insights = []
        if data_analyst_result.get("insights"):
            all_insights.extend([f"📊 {insight}" for insight in data_analyst_result["insights"]])
        if researcher_result.get("insights"):
            all_insights.extend([f"🔍 {insight}" for insight in researcher_result["insights"]])
        
        # Crea summary esecutivo se non presente
        final_report = copywriter_result.get("final_report", "")
        if not final_report and global_status == "completed":
            final_report = await self._create_fallback_report(data_analyst_result, researcher_result, original_query)
        
        # Struttura finale
        aggregated_result = {
            "session_id": session_id,
            "status": global_status,
            "query": original_query,
            "execution_summary": {
                "mode": results.get("execution_mode", "unknown"),
                "agents_completed": len([k for k, v in results.items() if isinstance(v, dict) and v.get("status") == "completed"]),
                "total_agents": 3,
                "execution_time": "N/A"  # TODO: implementa tracking tempo
            },
            "agent_results": {
                "data_analyst": data_analyst_result,
                "researcher": researcher_result, 
                "copywriter": copywriter_result
            },
            "consolidated_insights": all_insights[:10],
            "final_report": final_report,
            "executive_summary": copywriter_result.get("executive_summary", ""),
            "key_findings": copywriter_result.get("key_findings", []),
            "recommendations": copywriter_result.get("recommendations", []),
            "data_quality_score": data_analyst_result.get("data_quality_score", 0.0),
            "research_reliability_score": researcher_result.get("reliability_score", 0.0)
        }
        
        return aggregated_result
    
    async def _create_fallback_report(self, data_result: Dict[str, Any], research_result: Dict[str, Any], query: str) -> str:
        """
        Crea un report di fallback se il Copywriter non ha prodotto risultati
        """
        report_sections = [
            f"# Analysis Report: {query}\n",
            "## Executive Summary",
            f"This report provides analysis results for: {query}\n"
        ]
        
        # Sezione Data Analysis
        if data_result.get("insights"):
            report_sections.extend([
                "## Data Analysis Results",
                "Key quantitative insights:",
                *[f"- {insight}" for insight in data_result["insights"][:5]],
                ""
            ])
        
        # Sezione Research Results  
        if research_result.get("insights"):
            report_sections.extend([
                "## Research Findings", 
                "Market research insights:",
                *[f"- {insight}" for insight in research_result["insights"][:5]],
                ""
            ])
        
        # Raccomandazioni
        recommendations = []
        recommendations.extend(data_result.get("recommendations", [])[:3])
        recommendations.extend(research_result.get("recommendations", [])[:3])
        
        if recommendations:
            report_sections.extend([
                "## Strategic Recommendations",
                *[f"- {rec}" for rec in recommendations],
                ""
            ])
        
        report_sections.append("\n---\nReport generated by AI Agent Orchestration Hub")
        
        return "\n".join(report_sections)
    
    async def close(self):
        """Chiude le connessioni e pulisce le risorse"""
        if self.memory_manager:
            await self.memory_manager.close()
        logger.info("Orchestrator resources closed")
