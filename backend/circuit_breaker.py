"""
Circuit Breaker Pattern
Temporarily stops requests to failing services and redirects to fallback mechanisms
"""

import logging
import asyncio
from typing import Callable, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Service is failing, reject requests
    HALF_OPEN = "half_open"     # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
    
    async def call(
        self, 
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN. Using fallback.")
                if fallback:
                    return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            
            if self.state == CircuitBreakerState.OPEN and fallback:
                logger.warning(f"Circuit breaker '{self.name}' - using fallback after failure")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            
            raise
    
    def _on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # Require 2 successes to close
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' recovered to CLOSED state")
    
    def _on_failure(self):
        """Handle failed request"""
        self.last_failure_time = datetime.now()
        self.failure_count += 1
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(f"Circuit breaker '{self.name}' opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state.value


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}
    
    def register(self, name: str, breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self.breakers[name] = breaker
        logger.info(f"Registered circuit breaker: {name}")
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)
    
    async def call(
        self,
        breaker_name: str,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Call function through circuit breaker"""
        breaker = self.get(breaker_name)
        if not breaker:
            logger.warning(f"Circuit breaker '{breaker_name}' not found")
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        return await breaker.call(func, *args, fallback=fallback, **kwargs)
    
    def get_status(self) -> dict:
        """Get status of all circuit breakers"""
        return {
            name: {
                "state": breaker.get_state(),
                "failures": breaker.failure_count,
                "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
            }
            for name, breaker in self.breakers.items()
        }


# Initialize global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def create_service_breakers():
    """Create circuit breakers for external services"""
    
    # LLM API circuit breaker
    llm_breaker = CircuitBreaker(
        name="llm_api",
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=Exception
    )
    circuit_breaker_manager.register("llm_api", llm_breaker)
    
    # Database circuit breaker
    db_breaker = CircuitBreaker(
        name="database",
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )
    circuit_breaker_manager.register("database", db_breaker)
    
    # External API circuit breaker
    api_breaker = CircuitBreaker(
        name="external_api",
        failure_threshold=4,
        recovery_timeout=45,
        expected_exception=Exception
    )
    circuit_breaker_manager.register("external_api", api_breaker)
    
    logger.info("Service circuit breakers created")
