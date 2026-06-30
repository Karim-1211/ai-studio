import threading
import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self):
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key, limit, window_seconds, now=None):
        now = time.monotonic() if now is None else float(now)
        limit = max(1, int(limit))
        window_seconds = max(1, int(window_seconds))
        threshold = now - window_seconds

        with self._lock:
            bucket = self._events[str(key)]
            while bucket and bucket[0] <= threshold:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return False, 0, retry_after

            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return True, remaining, 0

    def reset(self):
        with self._lock:
            self._events.clear()


rate_limiter = SlidingWindowRateLimiter()
