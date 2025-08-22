"""
Test Suite per FastAPI - AI Agent Orchestration Hub

Test di integrazione per API endpoints, orchestratore e workflow completo.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

# Import dell'app FastAPI
from api.main import app
from api.orchestrator import Orchestrator, ExecutionMode
from api.memory import MemoryManager


class TestHealthCheck:
    """Test per health check endpoint"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    def test_root_endpoint_returns_200(self):
        """Test che root endpoint ritorni status 200"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Agent Orchestration Hub"
        assert "version" in data
    
    def test_health_endpoint_structure(self):
        """Test struttura response health endpoint"""
        response = self.client.get("/health")
        assert response.status_code in [200, 503]  # Può fallire se Redis non è disponibile
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "components" in data


class TestAnalyzeEndpoint:
    """Test per endpoint /analyze principale"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    @patch('api.main.orchestrator')
    def test_analyze_with_valid_query(self, mock_orchestrator):
        """Test analyze endpoint con query valida"""
        # Mock orchestrator response
        mock_result = {
            "session_id": "test-session-123",
            "status": "completed",
            "query": "Analyze fintech market",
            "execution_summary": {"mode": "sequential", "agents_completed": 3, "total_agents": 3},
            "agent_results": {
                "data_analyst": {"status": "completed", "insights": ["Test insight"]},
                "researcher": {"status": "completed", "insights": ["Test research"]},
                "copywriter": {"status": "completed", "final_report": "Test report"}
            },
            "consolidated_insights": ["Test insight", "Test research"],
            "final_report": "Comprehensive analysis report...",
            "executive_summary": "Executive summary...",
            "key_findings": ["Finding 1", "Finding 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "data_quality_score": 0.85,
            "research_reliability_score": 0.90
        }
        
        mock_orchestrator.process_request = AsyncMock(return_value=mock_result)
        
        # Test request
        request_data = {"query": "Analyze fintech market in Europe"}
        response = self.client.post("/analyze", json=request_data)
        
        # Verifica response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["query"] == "Analyze fintech market in Europe"
        assert "session_id" in data
        assert "final_report" in data
        assert "executive_summary" in data
    
    def test_analyze_with_invalid_query(self):
        """Test analyze endpoint con query non valida"""
        # Query troppo corta
        response = self.client.post("/analyze", json={"query": "hi"})
        assert response.status_code == 422
        
        # Query mancante
        response = self.client.post("/analyze", json={})
        assert response.status_code == 422
        
        # Payload malformato
        response = self.client.post("/analyze", data="invalid json")
        assert response.status_code == 422
    
    def test_analyze_with_execution_mode(self):
        """Test analyze endpoint con execution mode specificato"""
        with patch('api.main.orchestrator') as mock_orchestrator:
            mock_result = {
                "session_id": "test-session-456",
                "status": "completed",
                "query": "Test query",
                "execution_summary": {"mode": "parallel", "agents_completed": 3, "total_agents": 3},
                "agent_results": {"data_analyst": {}, "researcher": {}, "copywriter": {}},
                "consolidated_insights": [],
                "final_report": "Test report",
                "executive_summary": "Test summary",
                "key_findings": [],
                "recommendations": [],
                "data_quality_score": 0.0,
                "research_reliability_score": 0.0
            }
            mock_orchestrator.process_request = AsyncMock(return_value=mock_result)
            
            request_data = {
                "query": "Test query with parallel execution",
                "execution_mode": "parallel"
            }
            response = self.client.post("/analyze", json=request_data)
            
            assert response.status_code == 200
            # Verifica che il mode sia stato passato correttamente
            mock_orchestrator.process_request.assert_called_once()
            args = mock_orchestrator.process_request.call_args
            assert args[1] == ExecutionMode.PARALLEL  # execution_mode parameter
    
    def test_analyze_with_invalid_execution_mode(self):
        """Test analyze endpoint con execution mode non valido"""
        request_data = {
            "query": "Test query",
            "execution_mode": "invalid_mode"
        }
        response = self.client.post("/analyze", json=request_data)
        assert response.status_code == 400
        assert "Invalid execution mode" in response.json()["detail"]


class TestSessionStatus:
    """Test per endpoint status sessione"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    @patch('api.main.orchestrator')
    def test_get_session_status_existing(self, mock_orchestrator):
        """Test recupero status sessione esistente"""
        # Mock memory manager responses
        mock_memory = Mock()
        mock_memory.get_full_context = AsyncMock(return_value={
            "original_query": "Test query",
            "execution_mode": "sequential"
        })
        mock_memory.get_agent_outputs = AsyncMock(return_value={
            "data_analyst": {"status": "completed"},
            "researcher": {"status": "completed"}
        })
        mock_orchestrator.memory_manager = mock_memory
        
        response = self.client.get("/status/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["original_query"] == "Test query"
        assert data["agents_completed"] == 2
        assert data["total_agents"] == 3
    
    @patch('api.main.orchestrator')  
    def test_get_session_status_not_found(self, mock_orchestrator):
        """Test recupero status sessione non esistente"""
        mock_memory = Mock()
        mock_memory.get_full_context = AsyncMock(return_value={})
        mock_orchestrator.memory_manager = mock_memory
        
        response = self.client.get("/status/nonexistent-session")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestAgentsInfo:
    """Test per endpoint informazioni agenti"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    def test_get_agents_info(self):
        """Test recupero informazioni agenti"""
        response = self.client.get("/agents/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica struttura response
        assert "agents" in data
        assert "orchestration_modes" in data
        
        # Verifica agenti
        agents = data["agents"]
        assert "data_analyst" in agents
        assert "researcher" in agents
        assert "copywriter" in agents
        
        # Verifica ogni agente ha le informazioni necessarie
        for agent_name, agent_info in agents.items():
            assert "name" in agent_info
            assert "description" in agent_info
            assert "capabilities" in agent_info
            assert isinstance(agent_info["capabilities"], list)


class TestRequestValidation:
    """Test per validazione input requests"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    def test_request_schema_validation(self):
        """Test validazione schema request"""
        # Query troppo lunga
        long_query = "x" * 1001
        response = self.client.post("/analyze", json={"query": long_query})
        assert response.status_code == 422
        
        # Query con caratteri speciali (dovrebbe essere accettata)
        special_query = "Analyze market with symbols: $, %, @, #"
        with patch('api.main.orchestrator') as mock_orchestrator:
            mock_result = {
                "session_id": "test",
                "status": "completed",
                "query": special_query,
                "execution_summary": {},
                "agent_results": {},
                "consolidated_insights": [],
                "final_report": "",
                "executive_summary": "",
                "key_findings": [],
                "recommendations": [],
                "data_quality_score": 0.0,
                "research_reliability_score": 0.0
            }
            mock_orchestrator.process_request = AsyncMock(return_value=mock_result)
            
            response = self.client.post("/analyze", json={"query": special_query})
            assert response.status_code == 200


class TestErrorHandling:
    """Test per gestione errori globale"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.client = TestClient(app)
    
    @patch('api.main.orchestrator')
    def test_orchestrator_error_handling(self, mock_orchestrator):
        """Test gestione errori dall'orchestratore"""
        mock_orchestrator.process_request = AsyncMock(side_effect=Exception("Test error"))
        
        request_data = {"query": "Test query"}
        response = self.client.post("/analyze", json=request_data)
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_orchestrator_not_initialized(self):
        """Test gestione orchestratore non inizializzato"""
        with patch('api.main.orchestrator', None):
            response = self.client.post("/analyze", json={"query": "Test"})
            assert response.status_code == 503
            assert "Orchestrator not initialized" in response.json()["detail"]


# Fixtures per test asincroni
@pytest.fixture
def mock_orchestrator():
    """Fixture per mock orchestrator"""
    mock = Mock()
    mock.process_request = AsyncMock()
    mock.memory_manager = Mock()
    return mock


@pytest.fixture
def sample_analysis_request():
    """Fixture per richiesta di analisi sample"""
    return {
        "query": "Analyze the fintech market in Europe for 2024",
        "execution_mode": "sequential"
    }


@pytest.fixture  
def sample_analysis_response():
    """Fixture per risposta di analisi sample"""
    return {
        "session_id": "test-session-123",
        "status": "completed", 
        "query": "Analyze the fintech market in Europe for 2024",
        "execution_summary": {
            "mode": "sequential",
            "agents_completed": 3,
            "total_agents": 3,
            "execution_time": "N/A"
        },
        "agent_results": {
            "data_analyst": {
                "status": "completed",
                "kpis": {"market_growth": 15.2, "adoption_rate": 34.5},
                "insights": ["Strong growth in digital payments", "Regulatory compliance improving"]
            },
            "researcher": {
                "status": "completed",
                "sources": ["McKinsey Report 2024", "EU Fintech Analysis"],
                "insights": ["Brexit impact stabilizing", "New regulation framework"]
            },
            "copywriter": {
                "status": "completed",
                "final_report": "Comprehensive fintech analysis...",
                "executive_summary": "European fintech market shows robust growth..."
            }
        },
        "consolidated_insights": [
            "📊 Strong growth in digital payments",
            "🔍 Brexit impact stabilizing"  
        ],
        "final_report": "# European Fintech Market Analysis 2024\n\n...",
        "executive_summary": "The European fintech market demonstrates robust growth...",
        "key_findings": [
            "Market growth rate: 15.2%",
            "Digital adoption increasing significantly"
        ],
        "recommendations": [
            "Focus on regulatory compliance",
            "Expand digital payment solutions"
        ],
        "data_quality_score": 0.85,
        "research_reliability_score": 0.92
    }
