"""
Base Agent

Classe base astratta per tutti gli agenti specializzati del sistema.
Definisce l'interfaccia comune e le funzionalità condivise.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import uuid
from loguru import logger
import os
from openai import AsyncOpenAI


class AgentType(Enum):
    """Tipi di agenti disponibili"""
    DATA_ANALYST = "data_analyst"
    RESEARCHER = "researcher"
    COPYWRITER = "copywriter"


class AgentStatus(Enum):
    """Stati di esecuzione dell'agente"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class BaseAgent(ABC):
    """
    Classe base astratta per tutti gli agenti AI specializzati
    """
    
    def __init__(self, agent_type: AgentType, memory_manager=None):
        """
        Inizializza l'agente base
        
        Args:
            agent_type: Tipo di agente
            memory_manager: Gestore della memoria condivisa
        """
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.memory_manager = memory_manager
        self.session_id = None
        
        # Inizializza client OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, using mock responses")
            self.openai_client = None
        else:
            self.openai_client = AsyncOpenAI(api_key=api_key)
    
    async def run(self, input_data: str, session_id: str = None) -> Dict[str, Any]:
        """
        Esegue l'elaborazione dell'agente
        
        Args:
            input_data: Dati di input da processare
            session_id: ID sessione per context sharing
            
        Returns:
            Risultati dell'elaborazione
        """
        self.session_id = session_id or str(uuid.uuid4())
        
        try:
            self._update_status(AgentStatus.RUNNING)
            logger.info(f"Starting {self.agent_type.value} processing")
            
            # Carica contesto condiviso
            context = await self.load_context()
            
            # Processa i dati
            result = await self.process(input_data, context)
            
            # Memorizza il risultato
            await self.store_result(result)
            
            self._update_status(AgentStatus.COMPLETED)
            logger.info(f"Completed {self.agent_type.value} processing")
            
            return result
            
        except Exception as e:
            self._update_status(AgentStatus.ERROR)
            logger.error(f"Error in {self.agent_type.value}: {e}")
            return {
                "agent": self.agent_type.value,
                "status": "error",
                "error": str(e),
                "result": None
            }
    
    async def load_context(self) -> Optional[Dict[str, Any]]:
        """Carica il contesto dalla memoria condivisa"""
        if self.memory_manager and self.session_id:
            return await self.memory_manager.get_full_context(self.session_id)
        return {}
    
    async def store_result(self, result: Dict[str, Any]) -> bool:
        """Memorizza il risultato nella memoria condivisa"""
        if self.memory_manager and self.session_id:
            return await self.memory_manager.store_agent_output(
                self.session_id, self.agent_type.value, result
            )
        return False
    
    async def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """
        Effettua una chiamata al modello LLM
        
        Args:
            prompt: Prompt utente
            system_prompt: System prompt specifico
            
        Returns:
            Risposta del modello
        """
        if not self.openai_client:
            # Mock response per testing senza API key
            return f"Mock response from {self.agent_type.value} for prompt: {prompt[:100]}..."
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return f"Error generating response: {e}"
    
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa una richiesta specifica per questo agente
        
        Args:
            query: Query da processare
            context: Contesto aggiuntivo dalla memoria condivisa
            
        Returns:
            Dizionario con risultati dell'elaborazione
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Restituisce il system prompt specifico per questo agente
        
        Returns:
            System prompt ottimizzato per il ruolo dell'agente
        """
        pass
    
    def _update_status(self, status: AgentStatus):
        """Aggiorna lo stato dell'agente"""
        self.status = status
        logger.debug(f"{self.agent_type.value} status changed to {status.value}")
