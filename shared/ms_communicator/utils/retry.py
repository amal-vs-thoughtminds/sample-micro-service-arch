import time
from typing import Callable, Any, Optional, Type
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log
)
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        exceptions: tuple[Type[Exception], ...] = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.exceptions = exceptions
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False

    def _can_retry(self) -> bool:
        if not self.is_open:
            return True
        
        if self.last_failure_time and \
           datetime.now() - self.last_failure_time > timedelta(seconds=self.reset_timeout):
            self.is_open = False
            self.failures = 0
            return True
        
        return False

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failures} failures")

    def record_success(self) -> None:
        self.failures = 0
        self.is_open = False
        self.last_failure_time = None

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self._can_retry():
                raise CircuitBreakerError("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except self.exceptions as e:
                self.record_failure()
                raise
        return wrapper

def create_retry_decorator(
    max_attempts: int = 3,
    delay: float = 1.0,
    strategy: str = "exponential",
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Create a retry decorator with the specified configuration
    """
    wait_strategies = {
        "linear": wait_fixed(delay),
        "exponential": wait_exponential(multiplier=delay),
        "fibonacci": wait_fixed(delay)  # Implement fibonacci if needed
    }
    
    wait_strategy = wait_strategies.get(strategy, wait_exponential(multiplier=delay))
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_strategy,
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True
    )

class RetryManager:
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        strategy: str = "exponential",
        exceptions: tuple[Type[Exception], ...] = (Exception,),
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.strategy = strategy
        self.exceptions = exceptions
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.retry_decorator = create_retry_decorator(
            max_attempts=max_attempts,
            delay=delay,
            strategy=strategy,
            exceptions=exceptions
        )

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        @self.circuit_breaker
        @self.retry_decorator
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)
        return wrapper 