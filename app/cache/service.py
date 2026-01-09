"""Redis cache service."""
import json
import pickle
from typing import Any, Dict, List, Optional
import redis
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AgentManifest, AgentInstallation


class CacheService:
    """Redis cache service for hot path data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=False)
    
    def get_agent_manifest(self, agent_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Get agent manifest from cache.
        
        Args:
            agent_id: Agent ID
            version: Agent version
            
        Returns:
            Manifest dict or None
        """
        key = f"manifest:{agent_id}:{version}"
        data = self.redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def set_agent_manifest(self, agent_id: str, version: str, manifest: Dict[str, Any]):
        """Cache agent manifest.
        
        Args:
            agent_id: Agent ID
            version: Agent version
            manifest: Manifest dict
        """
        key = f"manifest:{agent_id}:{version}"
        self.redis_client.setex(key, 3600, pickle.dumps(manifest))  # 1 hour TTL
    
    def get_user_installations(self, user_id) -> Optional[List[AgentInstallation]]:
        """Get user installations from cache.
        
        Args:
            user_id: User ID (UUID or string)
            
        Returns:
            List of installations or None
        """
        key = f"installations:{str(user_id)}"
        data = self.redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def set_user_installations(self, user_id, installations: List[AgentInstallation]):
        """Cache user installations.
        
        Args:
            user_id: User ID (UUID or string)
            installations: List of installations
        """
        key = f"installations:{str(user_id)}"
        self.redis_client.setex(key, 300, pickle.dumps(installations))  # 5 min TTL
    
    def get_shared_context(self, user_id) -> Optional[Dict[str, Any]]:
        """Get shared context from cache.
        
        Args:
            user_id: User ID (UUID or string)
            
        Returns:
            Shared context dict or None
        """
        key = f"shared_context:{str(user_id)}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set_shared_context(self, user_id, context: Dict[str, Any]):
        """Cache shared context.
        
        Args:
            user_id: User ID (UUID or string)
            context: Shared context dict
        """
        key = f"shared_context:{str(user_id)}"
        self.redis_client.setex(key, 300, json.dumps(context))  # 5 min TTL
    
    def invalidate_user_installations(self, user_id):
        """Invalidate user installations cache.
        
        Args:
            user_id: User ID (UUID or string)
        """
        key = f"installations:{str(user_id)}"
        self.redis_client.delete(key)
    
    def invalidate_shared_context(self, user_id):
        """Invalidate shared context cache.
        
        Args:
            user_id: User ID (UUID or string)
        """
        key = f"shared_context:{str(user_id)}"
        self.redis_client.delete(key)
