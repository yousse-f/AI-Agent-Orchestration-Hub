"""
FastAPI Main Application

Entry point dell'API REST per il sistema multi-agent orchestrato.
Espone gli endpoints per ricevere richieste di analisi e coordinare
l'esecuzione degli agenti specializzati.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn
from loguru import logger
import sys
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

from .orchestrator import Orchestrator, ExecutionMode

# Configurazione logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# Orchestrator globale
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione lifecycle dell'applicazione"""
    global orchestrator
    
    # Startup
    logger.info("Starting AI Agent Orchestration Hub...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    orchestrator = Orchestrator(redis_url)
    logger.info("Orchestrator initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent Orchestration Hub...")
    if orchestrator:
        await orchestrator.close()
    logger.info("Shutdown complete")


# Modelli Pydantic per request/response
class AnalysisRequest(BaseModel):
    """Modello per richieste di analisi"""
    query: str = Field(..., description="Query da analizzare", min_length=3, max_length=1000)
    execution_mode: Optional[str] = Field(None, description="Modalità di esecuzione: sequential, parallel, dynamic")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Opzioni aggiuntive")


class AnalysisResponse(BaseModel):
    """Modello per response di analisi"""
    session_id: str
    status: str
    query: str
    execution_summary: Dict[str, Any]
    agent_results: Dict[str, Any]
    consolidated_insights: list
    final_report: str
    executive_summary: str
    key_findings: list
    recommendations: list
    data_quality_score: float
    research_reliability_score: float


class HealthResponse(BaseModel):
    """Modello per health check response"""
    status: str
    service: str
    version: str
    components: Dict[str, str]


# Inizializza FastAPI app
app = FastAPI(
    title="AI Agent Orchestration Hub",
    description="Sistema multi-agent per analisi e report automatizzati con orchestrazione intelligente",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint con informazioni di base"""
    return HealthResponse(
        status="healthy",
        service="AI Agent Orchestration Hub",
        version="1.0.0",
        components={
            "api": "running",
            "orchestrator": "initialized",
            "agents": "3 available"
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint completo
    
    Verifica lo stato dell'API, orchestratore e connessioni esterne
    """
    try:
        # Verifica orchestrator
        orchestrator_status = "healthy" if orchestrator else "not_initialized"
        
        # Verifica connessione Redis (se possibile)
        redis_status = "unknown"
        if orchestrator and orchestrator.memory_manager:
            try:
                # Test semplice di connessione Redis
                await orchestrator.memory_manager.store_context("health_check", "test", {"timestamp": "now"}, ttl=10)
                redis_status = "connected"
            except Exception:
                redis_status = "connection_error"
        
        # Verifica agenti
        agents_status = "ready" if orchestrator else "not_initialized"
        
        components = {
            "orchestrator": orchestrator_status,
            "redis": redis_status,
            "agents": agents_status,
            "data_analyst": "ready" if orchestrator else "not_ready",
            "researcher": "ready" if orchestrator else "not_ready", 
            "copywriter": "ready" if orchestrator else "not_ready"
        }
        
        # Determina stato globale
        overall_status = "healthy" if all(status not in ["error", "connection_error", "not_initialized"] 
                                         for status in components.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            service="AI Agent Orchestration Hub",
            version="1.0.0",
            components=components
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service health check failed")


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_request(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principale per richieste di analisi multi-agent
    
    Accetta una query utente, orchestrated gli agenti AI specializzati
    e restituisce un'analisi completa con report finale.
    
    Args:
        request: Richiesta di analisi con query e opzioni
        
    Returns:
        Risultato strutturato con analisi di tutti gli agenti
        
    Raises:
        HTTPException: Per errori di validazione o processing
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Received analysis request: {request.query[:100]}...")
        
        # Valida e converti execution mode
        execution_mode = None
        if request.execution_mode:
            try:
                execution_mode = ExecutionMode(request.execution_mode.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid execution mode: {request.execution_mode}. Valid options: sequential, parallel, dynamic"
                )
        
        # Processa la richiesta
        result = await orchestrator.process_request(request.query, execution_mode)
        
        # Converti risultato nel modello response
        response = AnalysisResponse(
            session_id=result["session_id"],
            status=result["status"],
            query=result["query"],
            execution_summary=result["execution_summary"],
            agent_results=result["agent_results"],
            consolidated_insights=result["consolidated_insights"],
            final_report=result["final_report"],
            executive_summary=result["executive_summary"],
            key_findings=result["key_findings"],
            recommendations=result["recommendations"],
            data_quality_score=result["data_quality_score"],
            research_reliability_score=result["research_reliability_score"]
        )
        
        logger.info(f"Successfully completed analysis for session {result['session_id']}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing analysis request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/status/{session_id}")
async def get_session_status(session_id: str):
    """
    Recupera lo stato di una sessione di analisi
    
    Args:
        session_id: ID della sessione da verificare
        
    Returns:
        Stato della sessione e informazioni di base
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Recupera contesto della sessione
        context = await orchestrator.memory_manager.get_full_context(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Recupera output degli agenti
        agent_outputs = await orchestrator.memory_manager.get_agent_outputs(session_id)
        
        return {
            "session_id": session_id,
            "original_query": context.get("original_query", "unknown"),
            "execution_mode": context.get("execution_mode", "unknown"),
            "agent_status": {
                "data_analyst": "completed" if "data_analyst" in agent_outputs else "pending",
                "researcher": "completed" if "researcher" in agent_outputs else "pending",
                "copywriter": "completed" if "copywriter" in agent_outputs else "pending"
            },
            "agents_completed": len(agent_outputs),
            "total_agents": 3
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving session status")


@app.get("/agents/info")
async def get_agents_info():
    """
    Informazioni sugli agenti disponibili
    
    Returns:
        Descrizione e capabilities di tutti gli agenti
    """
    return {
        "agents": {
            "data_analyst": {
                "name": "Data Analyst Agent",
                "description": "Specializzato in analisi dati, calcolo KPI e insights quantitativi",
                "capabilities": [
                    "Statistical analysis",
                    "KPI calculation", 
                    "Trend identification",
                    "Data quality assessment",
                    "Quantitative insights generation"
                ]
            },
            "researcher": {
                "name": "Researcher Agent", 
                "description": "Specializzato in ricerca informazioni e analisi qualitativa",
                "capabilities": [
                    "Market research",
                    "Information gathering",
                    "Source validation",
                    "Competitive analysis",
                    "Trend analysis"
                ]
            },
            "copywriter": {
                "name": "Copywriter Agent",
                "description": "Specializzato in creazione report e sintesi narrative",
                "capabilities": [
                    "Report generation",
                    "Executive summaries",
                    "Content synthesis",
                    "Narrative structure",
                    "Actionable recommendations"
                ]
            }
        },
        "orchestration_modes": {
            "sequential": "Agenti eseguiti in sequenza per massima coerenza",
            "parallel": "Agenti eseguiti in parallelo per velocità ottimizzata",
            "dynamic": "Strategia di esecuzione adattiva basata sulla query"
        }
    }


# Endpoint di utilità per debugging (solo in sviluppo)
if os.getenv("ENVIRONMENT", "development") == "development":
    
    @app.get("/debug/memory/{session_id}")
    async def debug_memory(session_id: str):
        """Debug: visualizza contenuto memoria sessione"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        context = await orchestrator.memory_manager.get_full_context(session_id)
        return {"session_id": session_id, "context": context}
    
    @app.delete("/debug/memory/{session_id}")
    async def debug_clear_memory(session_id: str):
        """Debug: pulisce memoria sessione"""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        success = await orchestrator.memory_manager.clear_context(session_id)
        return {"session_id": session_id, "cleared": success}


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    # Configurazione per sviluppo locale
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting AI Agent Orchestration Hub on {host}:{port}")
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )
