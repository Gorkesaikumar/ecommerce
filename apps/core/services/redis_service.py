import time
import uuid
import logging
from django.core.cache import cache
from django_redis import get_redis_connection
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RedisService:
    """
    Central utility for Redis operations: Locking, Rate Limiting, Idempotency.
    """
    
    KEY_PREFIX = "ecom:"

    @staticmethod
    def get_lock_key(resource_type: str, resource_id: str) -> str:
        return f"{RedisService.KEY_PREFIX}lock:{resource_type}:{resource_id}"

    @staticmethod
    def get_idempotency_key(scope: str, key_id: str) -> str:
        return f"{RedisService.KEY_PREFIX}idempotency:{scope}:{key_id}"

    @staticmethod
    @contextmanager
    def acquire_lock(resource_type: str, resource_id: str, timeout: int = 30, blocking_timeout: int = 5):
        """
        Distributed Lock using Redis SETNX.
        :param timeout: Time in seconds after which lock auto-expires (deadlock prevention).
        :param blocking_timeout: Time to wait to acquire lock before giving up.
        """
        lock_key = RedisService.get_lock_key(resource_type, resource_id)
        lock_value = str(uuid.uuid4())
        con = get_redis_connection("default")
        
        start_time = time.time()
        acquired = False
        
        try:
            while time.time() - start_time < blocking_timeout:
                if con.set(lock_key, lock_value, nx=True, ex=timeout):
                    acquired = True
                    break
                time.sleep(0.1)
            
            if not acquired:
                raise Exception(f"Could not acquire lock for {resource_type}:{resource_id}")
            
            yield True
            
        finally:
            if acquired:
                # Release lock only if we own it
                script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
                """
                con.eval(script, 1, lock_key, lock_value)

    @staticmethod
    def check_and_set_idempotency_key(scope: str, key_id: str, ttl: int = 86400) -> bool:
        """
        Returns True if key was set (New Event).
        Returns False if key already existed (Duplicate Event).
        """
        redis_key = RedisService.get_idempotency_key(scope, key_id)
        con = get_redis_connection("default")
        # SETNX equivalent
        was_set = con.set(redis_key, "PROCESSED", nx=True, ex=ttl)
        return bool(was_set)
