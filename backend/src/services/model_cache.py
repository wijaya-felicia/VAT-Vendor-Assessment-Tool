from typing import Dict, Any, Optional, Tuple
import time
import threading
from datetime import datetime, timedelta

import arviz as az


class ModelCache:
    
    def __init__(self, ttl_minutes: int = 60):
        self.ttl_minutes = ttl_minutes
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id not in self._cache:
                return None
            
            entry = self._cache[session_id]
            
            if datetime.utcnow() > entry["expires_at"]:
                del self._cache[session_id]
                return None
            
            return entry["models"]
    
    def set(
        self, 
        session_id: str, 
        price_idata: Any,
        timeliness_idata: Any,
        mcmc_iterations: int,
        mcmc_chains: int,
        mcmc_tuning: int,
    ) -> None:
        with self._lock:
            self._cache[session_id] = {
                "models": {
                    "price_idata": price_idata,
                    "timeliness_idata": timeliness_idata,
                },
                "config": {
                    "mcmc_iterations": mcmc_iterations,
                    "mcmc_chains": mcmc_chains,
                    "mcmc_tuning": mcmc_tuning,
                },
                "cached_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=self.ttl_minutes),
            }
    
    def clear(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._cache:
                del self._cache[session_id]
    
    def clear_all(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        with self._lock:
            return len(self._cache)


_model_cache = ModelCache(ttl_minutes=60)


def get_model_cache() -> ModelCache:
    return _model_cache
