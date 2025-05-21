import asyncio
import logging
from asyncio import Queue
from typing import List

import aiohttp

from config import QUEUE_MAXSIZE, CONSUMER_COUNT
from fetcher import fetch
from writer import save_to_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def producer(queue: Queue, urls: List[str]) -> None:
    """
    Produces tasks by fetching data from URLs and placing results in a queue.

    Args:
        queue (Queue): The queue to place fetched results into.
        urls (List[str]): The list of URLs to fetch.
    """
    async with aiohttp.ClientSession() as session:
        for url in urls:
            result = await fetch(session, url)
            await queue.put(result)
            logger.info("📥 Enqueued result for: %s (Queue size: %d)", url, queue.qsize())

        # Send sentinel values to signal consumers to stop
        for _ in range(CONSUMER_COUNT):
            await queue.put(None)


async def consumer(queue: Queue, consumer_id: int) -> None:
    """
    Consumes items from the queue and saves them in batches to the database.

    Args:
        queue (Queue): The queue to consume results from.
        consumer_id (int): An identifier for the consumer instance.
    """
    buffer = []

    while True:
        item = await queue.get()
        if item is None:
            break

        buffer.append(item)

        if len(buffer) >= 10:
            await save_to_db(buffer)
            buffer.clear()

        logger.info("🔄 Consumer %d processed item. Queue size: %d", consumer_id, queue.qsize())

    # Save remaining items in buffer
    if buffer:
        await save_to_db(buffer)

    logger.info("✅ Consumer %d exiting.", consumer_id)


async def main() -> None:
    """
    Main function to coordinate producers and consumers.
    """
    urls = [f"https://httpbin.org/status/{code}" for code in range(1, 50)]
    queue = Queue(maxsize=QUEUE_MAXSIZE)

    producers = [asyncio.create_task(producer(queue, urls))]
    consumers = [asyncio.create_task(consumer(queue, i)) for i in range(CONSUMER_COUNT)]

    await asyncio.gather(*producers)
    await asyncio.gather(*consumers)


if __name__ == "__main__":
    asyncio.run(main())
