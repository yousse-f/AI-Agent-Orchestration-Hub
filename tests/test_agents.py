"""
Test Suite per Agenti AI - AI Agent Orchestration Hub

Test unitari per tutti gli agenti specializzati e orchestratore.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

from api.agents.base_agent import BaseAgent, AgentType, AgentStatus
from api.agents.data_analyst import DataAnalystAgent
from api.agents.researcher import ResearcherAgent
from api.agents.copywriter import CopywriterAgent
from api.orchestrator import Orchestrator, ExecutionMode
from api.memory import MemoryManager


class TestBaseAgent:
    """Test per classe base astratta BaseAgent"""
    
    def test_base_agent_cannot_be_instantiated(self):
        """Test che BaseAgent non può essere istanziata direttamente"""
        with pytest.raises(TypeError):
            BaseAgent(AgentType.DATA_ANALYST)
    
    def test_agent_initialization(self):
        """Test inizializzazione corretta degli agenti concreti"""
        agent = DataAnalystAgent()
        assert agent.agent_type == AgentType.DATA_ANALYST
        assert agent.status == AgentStatus.IDLE
        assert agent.session_id is None
    
    def test_agent_status_transitions(self):
        """Test transizioni di stato agente"""
        agent = DataAnalystAgent()
        
        # Stato iniziale
        assert agent.status == AgentStatus.IDLE
        
        # Transizione a RUNNING
        agent._update_status(AgentStatus.RUNNING)
        assert agent.status == AgentStatus.RUNNING
        
        # Transizione a COMPLETED
        agent._update_status(AgentStatus.COMPLETED)
        assert agent.status == AgentStatus.COMPLETED


class TestDataAnalystAgent:
    """Test per Data Analyst Agent"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.mock_memory = Mock()
        self.agent = DataAnalystAgent(self.mock_memory)
    
    @pytest.mark.asyncio
    async def test_process_with_fintech_query(self):
        """Test processamento query fintech"""
        query = "Analyze fintech market growth and KPIs"
        
        # Mock LLM response
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Fintech market showing 25% YoY growth with strong adoption rates."
            
            result = await self.agent.process(query)
            
            # Verifica struttura risultato
            assert result["agent"] == "data_analyst"
            assert result["status"] == "completed"
            assert result["query"] == query
            assert "analysis" in result
            assert "kpis" in result
            assert "insights" in result
            assert "confidence_score" in result
    
    @pytest.mark.asyncio
    async def test_kpi_calculation(self):
        """Test calcolo KPI specifici"""
        query = "Calculate revenue growth KPIs"
        
        result = await self.agent._calculate_kpis({}, query)
        
        # Verifica che vengano calcolati KPI appropriati
        assert isinstance(result, dict)
        if "revenue" in query.lower():
            assert "revenue_growth_yoy" in result
            assert "profit_margin" in result
            assert "roi" in result
    
    def test_system_prompt_content(self):
        """Test contenuto system prompt"""
        prompt = self.agent.get_system_prompt()
        
        # Verifica che il prompt contenga elementi chiave
        assert "Data Analyst" in prompt
        assert "statistical analysis" in prompt.lower()
        assert "kpi" in prompt.lower()
        assert "quantitative" in prompt.lower()
    
    def test_parse_analysis_requirements(self):
        """Test parsing requirements dalla query"""
        query = "Analyze fintech revenue growth in Europe for 2024"
        requirements = self.agent._parse_analysis_requirements(query)
        
        assert requirements["industry"] == "fintech"
        assert requirements["geographic_scope"] == "europe" 
        assert "revenue" in requirements["metrics_requested"]
        assert "growth" in requirements["metrics_requested"]


class TestResearcherAgent:
    """Test per Researcher Agent"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.mock_memory = Mock()
        self.agent = ResearcherAgent(self.mock_memory)
    
    @pytest.mark.asyncio
    async def test_process_market_research_query(self):
        """Test processamento query di ricerca mercato"""
        query = "Research European fintech market trends and competitors"
        
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "European fintech market shows consolidation with key players expanding..."
            
            result = await self.agent.process(query)
            
            # Verifica struttura risultato
            assert result["agent"] == "researcher"
            assert result["status"] == "completed"
            assert result["query"] == query
            assert "search_strategy" in result
            assert "sources" in result
            assert "findings" in result
            assert "insights" in result
            assert "reliability_score" in result
    
    def test_analyze_search_requirements(self):
        """Test analisi requirements di ricerca"""
        query = "Market analysis of fintech competition in Europe"
        strategy = self.agent._analyze_search_requirements(query)
        
        assert strategy["search_type"] == "market_research"
        assert strategy["industry_sector"] == "fintech"
        assert strategy["geographic_focus"] == "Europe"
        assert "competitive_landscape" in strategy["focus_areas"]
    
    @pytest.mark.asyncio
    async def test_simulate_web_search(self):
        """Test simulazione ricerca web"""
        query = "fintech market research"
        strategy = {"industry_sector": "fintech", "geographic_focus": "Global"}
        
        sources = await self.agent._simulate_web_search(query, strategy)
        
        # Verifica che vengano generate fonti realistiche
        assert isinstance(sources, list)
        assert len(sources) <= self.agent.max_sources
        
        for source in sources:
            assert "title" in source
            assert "url" in source
            assert "source" in source
            assert "reliability" in source
            assert isinstance(source["reliability"], float)
            assert 0 <= source["reliability"] <= 1
    
    def test_extract_statistics_from_text(self):
        """Test estrazione statistiche dal testo"""
        text = "Market grew by 25% with $2.5 billion in funding and 150 million users"
        statistics = self.agent._extract_statistics(text)
        
        assert len(statistics) > 0
        # Verifica che vengano estratti numeri con contesto
        values = [stat["value"] for stat in statistics]
        assert any("25%" in value for value in values)
        assert any("billion" in value for value in values)


class TestCopywriterAgent:
    """Test per Copywriter Agent"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.mock_memory = Mock()
        self.agent = CopywriterAgent(self.mock_memory)
    
    @pytest.mark.asyncio
    async def test_process_report_generation(self):
        """Test generazione report finale"""
        query = "Analyze fintech market"
        context = {
            "agent_output:data_analyst": {
                "insights": ["Market growing 25%", "High adoption rates"],
                "kpis": {"growth_rate": 25.0, "adoption": 34.5}
            },
            "agent_output:researcher": {
                "insights": ["Strong competition", "Regulatory changes"],
                "sources": [{"title": "Fintech Report 2024", "reliability": 0.9}]
            }
        }
        
        with patch.object(self.agent, '_call_llm') as mock_llm:
            mock_llm.return_value = "Comprehensive fintech market analysis report..."
            
            result = await self.agent.process(query, context)
            
            # Verifica struttura risultato
            assert result["agent"] == "copywriter"
            assert result["status"] == "completed"
            assert result["query"] == query
            assert "final_report" in result
            assert "executive_summary" in result
            assert "key_findings" in result
            assert "recommendations" in result
            assert "report_metadata" in result
    
    def test_extract_agent_outputs(self):
        """Test estrazione output degli agenti dal contesto"""
        context = {
            "agent_output:data_analyst": {"test": "data"},
            "agent_output:researcher": {"test": "research"},
            "other_data": {"test": "other"}
        }
        
        outputs = self.agent._extract_agent_outputs(context)
        
        assert "data_analyst" in outputs
        assert "researcher" in outputs
        assert outputs["data_analyst"]["test"] == "data"
        assert outputs["researcher"]["test"] == "research"
    
    def test_determine_writing_style(self):
        """Test determinazione stile di scrittura"""
        # Query per executive
        query = "Executive summary for board presentation"
        style = self.agent._determine_writing_style(query, {})
        assert style["tone"] == "executive"
        assert style["audience"] == "senior_management"
        
        # Query tecnica
        query = "Detailed technical analysis of market data"
        style = self.agent._determine_writing_style(query, {})
        assert style["technical_level"] == "high"
    
    def test_calculate_reading_metrics(self):
        """Test calcolo metriche di lettura"""
        text = "This is a test report. It contains multiple sentences. And several paragraphs.\n\nSecond paragraph here."
        metrics = self.agent._calculate_reading_metrics(text)
        
        assert "word_count" in metrics
        assert "reading_time_minutes" in metrics
        assert "paragraph_count" in metrics
        assert metrics["word_count"] > 0
        assert metrics["reading_time_minutes"] >= 1


class TestOrchestrator:
    """Test per Orchestratore centrale"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.mock_memory = Mock()
        # Mock Redis per evitare dipendenze esterne nei test
        with patch('api.orchestrator.MemoryManager') as mock_memory_class:
            mock_memory_class.return_value = self.mock_memory
            self.orchestrator = Orchestrator()
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test esecuzione sequenziale agenti"""
        query = "Test sequential execution"
        session_id = "test-session"
        
        # Mock agent responses
        with patch.object(self.orchestrator.data_analyst, 'run') as mock_data, \
             patch.object(self.orchestrator.researcher, 'run') as mock_research, \
             patch.object(self.orchestrator.copywriter, 'run') as mock_copy:
            
            mock_data.return_value = {"agent": "data_analyst", "status": "completed"}
            mock_research.return_value = {"agent": "researcher", "status": "completed"}
            mock_copy.return_value = {"agent": "copywriter", "status": "completed"}
            
            result = await self.orchestrator._execute_sequential(query, session_id)
            
            # Verifica esecuzione sequenziale
            assert result["execution_mode"] == "sequential"
            assert result["execution_order"] == ["data_analyst", "researcher", "copywriter"]
            assert "data_analyst" in result
            assert "researcher" in result  
            assert "copywriter" in result
            
            # Verifica ordine di chiamata
            mock_data.assert_called_once()
            mock_research.assert_called_once()
            mock_copy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test esecuzione parallela agenti"""
        query = "Test parallel execution"
        session_id = "test-session"
        
        with patch.object(self.orchestrator.data_analyst, 'run') as mock_data, \
             patch.object(self.orchestrator.researcher, 'run') as mock_research, \
             patch.object(self.orchestrator.copywriter, 'run') as mock_copy:
            
            mock_data.return_value = {"agent": "data_analyst", "status": "completed"}
            mock_research.return_value = {"agent": "researcher", "status": "completed"}
            mock_copy.return_value = {"agent": "copywriter", "status": "completed"}
            
            result = await self.orchestrator._execute_parallel(query, session_id)
            
            # Verifica esecuzione parallela
            assert result["execution_mode"] == "parallel"
            assert "execution_phases" in result
            assert result["execution_phases"][0] == ["data_analyst", "researcher"]
            assert result["execution_phases"][1] == ["copywriter"]
    
    def test_determine_execution_strategy(self):
        """Test determinazione strategia esecuzione"""
        # Query che richiede analisi rapida
        quick_query = "Give me a quick summary of market trends"
        strategy = self.orchestrator._determine_execution_strategy(quick_query)
        assert strategy == ExecutionMode.PARALLEL
        
        # Query che richiede analisi approfondita  
        detailed_query = "Provide comprehensive detailed analysis of market"
        strategy = self.orchestrator._determine_execution_strategy(detailed_query)
        assert strategy == ExecutionMode.SEQUENTIAL
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test recovery da errori agenti"""
        query = "Test error handling"
        session_id = "test-session"
        
        with patch.object(self.orchestrator.data_analyst, 'run') as mock_data:
            # Simula errore del data analyst
            mock_data.side_effect = Exception("Data analyst error")
            
            result = await self.orchestrator._execute_sequential(query, session_id)
            
            # Verifica che l'errore sia gestito
            assert "error" in result
            assert "Data analyst error" in result["error"]


class TestMemoryManager:
    """Test per Memory Manager Redis"""
    
    def setup_method(self):
        """Setup per ogni test"""
        # Mock Redis per test unitari
        self.mock_redis = AsyncMock()
        with patch('api.memory.redis.from_url', return_value=self.mock_redis):
            self.memory = MemoryManager()
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_context(self):
        """Test storage e retrieval contesto"""
        session_id = "test-session"
        key = "test_key"
        data = {"test": "data", "number": 123}
        
        # Mock Redis operations
        self.mock_redis.setex = AsyncMock(return_value=True)
        self.mock_redis.get = AsyncMock(return_value='{"test": "data", "number": 123}')
        
        # Test storage
        success = await self.memory.store_context(session_id, key, data)
        assert success == True
        
        # Test retrieval
        retrieved = await self.memory.get_context(session_id, key)
        assert retrieved["test"] == "data"
        assert retrieved["number"] == 123
    
    @pytest.mark.asyncio
    async def test_agent_output_management(self):
        """Test gestione output agenti"""
        session_id = "test-session"
        agent_name = "data_analyst"
        output = {"result": "analysis complete", "kpis": {"growth": 25}}
        
        self.mock_redis.setex = AsyncMock(return_value=True)
        self.mock_redis.keys = AsyncMock(return_value=[f"session:{session_id}:agent_output:{agent_name}"])
        self.mock_redis.get = AsyncMock(return_value='{"result": "analysis complete", "kpis": {"growth": 25}}')
        
        # Test storage
        success = await self.memory.store_agent_output(session_id, agent_name, output)
        assert success == True
        
        # Test retrieval
        outputs = await self.memory.get_agent_outputs(session_id)
        assert agent_name in outputs
        assert outputs[agent_name]["result"] == "analysis complete"


# Fixtures
@pytest.fixture
def mock_memory_manager():
    """Fixture per mock memory manager"""
    mock = Mock()
    mock.store_context = AsyncMock(return_value=True)
    mock.get_context = AsyncMock(return_value=None)
    mock.get_full_context = AsyncMock(return_value={})
    mock.store_agent_output = AsyncMock(return_value=True)
    mock.get_agent_outputs = AsyncMock(return_value={})
    return mock


@pytest.fixture
def sample_query():
    """Fixture per query di test"""
    return "Analyze the fintech market in Europe for growth opportunities"


@pytest.fixture
def mock_llm_client():
    """Fixture per mock LLM client"""
    mock = Mock()
    mock.chat.completions.create = AsyncMock()
    mock.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="Mock LLM response for testing"))
    ]
    return mock


@pytest.fixture
def sample_agent_outputs():
    """Fixture per output degli agenti sample"""
    return {
        "data_analyst": {
            "agent": "data_analyst",
            "status": "completed",
            "insights": ["Market showing strong growth", "KPIs exceed expectations"],
            "kpis": {"growth_rate": 18.5, "market_share": 23.4},
            "confidence_score": 0.87
        },
        "researcher": {
            "agent": "researcher",  
            "status": "completed",
            "insights": ["New regulations favorable", "Competitive landscape consolidating"],
            "sources": [
                {"title": "EU Fintech Report 2024", "reliability": 0.92},
                {"title": "Market Analysis Q3", "reliability": 0.88}
            ],
            "reliability_score": 0.90
        },
        "copywriter": {
            "agent": "copywriter",
            "status": "completed", 
            "final_report": "# European Fintech Market Analysis\n\nExecutive Summary...",
            "executive_summary": "The European fintech market demonstrates...",
            "key_findings": ["Growth rate of 18.5%", "Market consolidation trend"],
            "recommendations": ["Expand in digital payments", "Focus on compliance"]
        }
    }
