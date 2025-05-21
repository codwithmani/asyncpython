import aiohttp
import asyncio
import logging
import time
from datetime import datetime

from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, RetryCallState

from config import RATE_LIMIT, TIME_PERIOD, RETRY_ATTEMPTS

# Configure logger
logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = AsyncLimiter(max_rate=RATE_LIMIT, time_period=TIME_PERIOD)

def log_retry(retry_state: RetryCallState) -> None:
    """
    Log retry attempts for a given URL.

    Args:
        retry_state (RetryCallState): The retry state containing attempt and arguments.
    """
    url = retry_state.args[1]  # Assuming the second argument is the URL
    attempt = retry_state.attempt_number
    logger.warning("🔁 Retry %s for URL: %s", attempt, url)


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential_jitter(initial=1, max=10),
    after=log_retry,
    reraise=True
)
async def fetch(session: aiohttp.ClientSession, url: str) -> dict:
    """
    Perform an HTTP GET request with retry and rate limiting.

    Args:
        session (aiohttp.ClientSession): The HTTP client session.
        url (str): The URL to fetch.

    Returns:
        dict: A dictionary with the URL, status, timestamp, and response time.
    """
    async with limiter:
        start_time = time.perf_counter()
        try:
            async with session.get(url, timeout=10) as response:
                elapsed = time.perf_counter() - start_time
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "url": url,
                    "status": response.status,
                    "response_time": round(elapsed, 3)
                }
        except Exception as exc:
            logger.error("❌ Failed: %s - Error: %s", url, exc)
            raise
