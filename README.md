<div align="center">

# 🤖 AI Agent Orchestration Hub

### *Production-Ready Multi-Agent AI System*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009485?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Redis-5.0+-dc382d?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ed?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

*Intelligent orchestration of specialized AI agents for comprehensive business analysis*

[🚀 Quick Start](#-quick-start) • [📖 API Docs](http://localhost:8000/docs) • [📧 Contact](#-contact)

</div>

---

## 🎯 **What It Does**

**AI Agent Orchestration Hub** coordinates three specialized AI agents to deliver comprehensive business intelligence:

- **📊 Data Analyst** - KPI calculation, statistical analysis, trend identification
- **🔍 Researcher** - Market intelligence, competitive analysis, source validation  
- **✍️ Copywriter** - Executive summaries, report synthesis, recommendations

**Key Features:** Multi-agent coordination • Redis memory sharing • REST API • Docker deployment • Production security

---

## 🚀 **Quick Start**

```bash
# One-command setup
git clone https://github.com/yousse-f/AI-Agent-Orchestration-Hub.git
cd AI-Agent-Orchestration-Hub
cp .env.example .env
# Add your OPENAI_API_KEY to .env
docker-compose up -d

# ✅ API running at http://localhost:8000
```

**Local Development:**
```bash
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 **API Usage**

**Analyze Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"query": "Analyze the European fintech market", "execution_mode": "sequential"}'
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "status": "completed",
  "agent_results": {
    "data_analyst": {"kpis": {...}, "insights": [...]},
    "researcher": {"sources": [...], "analysis": {...}},
    "copywriter": {"executive_summary": "...", "recommendations": [...]}
  },
  "final_report": "# Comprehensive Analysis Report\n...",
  "quality_metrics": {"data_quality_score": 0.89, "reliability_score": 0.94}
}
```

**Endpoints:** `/health` • `/analyze` • `/status/{session_id}` • `/agents/info` • `/docs`

---

## ⚙️ **Configuration**

**Environment:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
```

**Execution Modes:**
- `sequential` - Agents run in order (max coherence)
- `parallel` - Speed optimized execution  
- `dynamic` - AI-determined strategy

---

## 🛠️ **Tech Stack & Architecture**

```
Client → FastAPI → Orchestrator → [Data Analyst | Researcher | Copywriter] → Redis Memory → Response
```

**Built with:** Python 3.11+ • FastAPI • OpenAI GPT-4 • Redis • Docker • Pydantic • LangChain

**Features:** 
- ✅ Production-ready Docker deployment
- ✅ Comprehensive test coverage (95%+)
- ✅ Type safety with mypy
- ✅ Security hardening & non-root containers
- ✅ CI/CD pipeline with GitHub Actions

---

## 🧪 **Development**

```bash
# Testing
pytest tests/ --cov=api --cov-report=html

# Code quality
make lint security test

# Docker
docker-compose up -d
```

**Project Structure:**
```
ai-agent-orchestration-hub/
├── api/              # Core application
├── docker/           # Containerization  
├── tests/            # Test suite
├── .github/workflows # CI/CD pipeline
└── docs/             # Documentation
```

---

## 💼 **About**

> **Developed by [Yousse Ben Moussa](https://github.com/yousse-f)** - AI Engineer & MLOps Specialist
> 
> This project demonstrates expertise in multi-agent AI systems, production deployment, and enterprise-level software architecture.

**Use Cases:**
- 📊 Business intelligence automation
- 🔍 Investment research & analysis  
- 📋 Consulting report generation
- 🏢 Enterprise data analytics

---

## 📞 **Contact**

<div align="center">

**Yousse Ben Moussa** - AI Engineer & MLOps Specialist

[![GitHub](https://img.shields.io/badge/GitHub-yousse--f-181717?style=for-the-badge&logo=github)](https://github.com/yousse-f)
[![Email](https://img.shields.io/badge/Email-yussyjob@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:yussyjob@gmail.com)

📖 **[API Documentation](http://localhost:8000/docs)** • 🐛 **[Report Issues](https://github.com/yousse-f/AI-Agent-Orchestration-Hub/issues)**

⭐ **Star this repo if you found it useful!**

</div>

---

**License:** MIT • **Status:** Production Ready • **Contributions:** Welcome


