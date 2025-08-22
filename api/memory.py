"""
Memory Manager

Gestisce la memoria contestuale condivisa tramite Redis.
Permette agli agenti di leggere/scrivere contesto, prompt, output intermedi e history.
"""

from typing import Dict, Any, Optional, List
import json
import redis.asyncio as redis
from loguru import logger
import os
import asyncio
from datetime import datetime, timedelta


class MemoryManager:
    """
    Gestore della memoria condivisa Redis per il sistema multi-agent
    Con fallback in-memory se Redis non è disponibile
    """
    
    def __init__(self, redis_url: str = None):
        """
        Inizializza il connection manager Redis
        
        Args:
            redis_url: URL di connessione Redis
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        self.redis_url = redis_url
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour
        self.use_redis = True
        self.in_memory_store = {}  # Fallback in-memory store
        self.expiry_times = {}  # Track expiry times for in-memory data
        
    async def _get_redis_client(self):
        """Ottieni il client Redis con lazy initialization e fallback check"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test the connection
                await asyncio.wait_for(self.redis_client.ping(), timeout=2.0)
                self.use_redis = True
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory fallback")
                self.use_redis = False
                self.redis_client = None
        return self.redis_client
    
    def _cleanup_expired(self):
        """Remove expired entries from in-memory store"""
        current_time = datetime.now()
        expired_keys = [
            key for key, expiry in self.expiry_times.items() 
            if expiry <= current_time
        ]
        for key in expired_keys:
            self.in_memory_store.pop(key, None)
            self.expiry_times.pop(key, None)
    
    async def store_context(self, session_id: str, key: str, data: Any, ttl: int = None) -> bool:
        """
        Memorizza dati nel contesto di sessione
        
        Args:
            session_id: ID univoco della sessione
            key: Chiave per i dati
            data: Dati da memorizzare
            ttl: Time-to-live in secondi
            
        Returns:
            True se memorizzazione riuscita
        """
        redis_key = f"session:{session_id}:{key}"
        ttl = ttl or self.default_ttl
        
        try:
            redis_client = await self._get_redis_client()
            
            if self.use_redis and redis_client:
                # Use Redis
                serialized_data = json.dumps(data, default=str)
                await redis_client.setex(redis_key, ttl, serialized_data)
                logger.info(f"Stored context in Redis for session {session_id}, key {key}")
            else:
                # Use in-memory fallback
                self._cleanup_expired()
                self.in_memory_store[redis_key] = data
                self.expiry_times[redis_key] = datetime.now() + timedelta(seconds=ttl)
                logger.info(f"Stored context in memory for session {session_id}, key {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False
    
    async def get_context(self, session_id: str, key: str) -> Optional[Any]:
        """
        Recupera dati dal contesto di sessione
        
        Args:
            session_id: ID sessione
            key: Chiave dati
            
        Returns:
            Dati deserializzati o None se non trovati
        """
        redis_key = f"session:{session_id}:{key}"
        
        try:
            redis_client = await self._get_redis_client()
            
            if self.use_redis and redis_client:
                # Use Redis
                data = await redis_client.get(redis_key)
                if data is None:
                    return None
                return json.loads(data)
            else:
                # Use in-memory fallback
                self._cleanup_expired()
                return self.in_memory_store.get(redis_key)
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
    
    async def get_full_context(self, session_id: str) -> Dict[str, Any]:
        """Recupera tutto il contesto di una sessione"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"session:{session_id}:*"
            keys = await redis_client.keys(pattern)
            
            context = {}
            for key in keys:
                # Estrae il nome della chiave rimuovendo il prefisso
                context_key = key.split(":")[-1]
                data = await redis_client.get(key)
                if data:
                    context[context_key] = json.loads(data)
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving full context: {e}")
            return {}
    
    async def clear_context(self, session_id: str) -> bool:
        """Pulisce tutto il contesto di una sessione"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"session:{session_id}:*"
            keys = await redis_client.keys(pattern)
            
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared context for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing context: {e}")
            return False
    
    async def store_agent_output(self, session_id: str, agent_name: str, output: Any) -> bool:
        """Memorizza l'output di un agente specifico"""
        return await self.store_context(session_id, f"agent_output:{agent_name}", output)
    
    async def get_agent_outputs(self, session_id: str) -> Dict[str, Any]:
        """Recupera tutti gli output degli agenti per una sessione"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"session:{session_id}:agent_output:*"
            keys = await redis_client.keys(pattern)
            
            outputs = {}
            for key in keys:
                # Estrae il nome dell'agente
                agent_name = key.split(":")[-1]
                data = await redis_client.get(key)
                if data:
                    outputs[agent_name] = json.loads(data)
            
            return outputs
            
        except Exception as e:
            logger.error(f"Error retrieving agent outputs: {e}")
            return {}
    
    async def close(self):
        """Chiude la connessione Redis"""
        if self.redis_client:
            await self.redis_client.close()
