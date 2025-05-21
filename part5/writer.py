import aiosqlite
import logging

logger = logging.getLogger(__name__)


async def save_to_db(records: list[dict]) -> None:
    async with aiosqlite.connect("results.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                url TEXT,
                status INTEGER,
                response_time REAL
            )
        """)
        async with db.execute("BEGIN"):
            for record in records:
                if isinstance(record, dict):
                    await db.execute(
                        "INSERT INTO api_results (timestamp, url, status, response_time) VALUES (?, ?, ?, ?)",
                        (
                            record["timestamp"],
                            record["url"],
                            record["status"],
                            record["response_time"]
                        )
                    )
        await db.commit()
    logger.info("📦 All records saved to database.")
