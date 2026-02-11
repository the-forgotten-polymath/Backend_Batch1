"""Token bucket rate limiter implementation."""
import time
import threading


class TokenBucket:
    """Token bucket rate limiter for controlling request rates."""
    
    def __init__(self, rate, capacity=None):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens per second (requests per second)
            capacity: Maximum tokens in bucket (default: rate * 2)
        """
        self.rate = rate
        self.capacity = capacity if capacity else rate * 2
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens=1):
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add new tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens=1):
        """
        Wait until tokens are available and consume them.
        
        Args:
            tokens: Number of tokens to consume
        """
        while not self.consume(tokens):
            time.sleep(0.1)  # Sleep for 100ms and try again


class RateLimiterManager:
    """Manage rate limiters for multiple platforms."""
    
    def __init__(self, platform_rates):
        """
        Initialize rate limiter manager.
        
        Args:
            platform_rates: Dict mapping platform names to rates (requests/second)
        """
        self.limiters = {
            platform: TokenBucket(rate)
            for platform, rate in platform_rates.items()
        }
    
    def wait_for_platform(self, platform):
        """
        Wait for rate limit clearance for a platform.
        
        Args:
            platform: Platform name
        """
        if platform in self.limiters:
            self.limiters[platform].wait_for_token()
    
    def can_proceed(self, platform):
        """
        Check if a request can proceed for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            True if request can proceed, False otherwise
        """
        if platform in self.limiters:
            return self.limiters[platform].consume()
        return True
