from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def migrate_sqlite(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:

        def run(sync_conn):
            rows = sync_conn.execute(text("PRAGMA table_info(profiles)")).fetchall()
            cols = {row[1] for row in rows}
            if "rotation_order" not in cols:
                sync_conn.execute(text("ALTER TABLE profiles ADD COLUMN rotation_order INTEGER"))
            if "exclude_keywords" not in cols:
                sync_conn.execute(
                    text("ALTER TABLE profiles ADD COLUMN exclude_keywords VARCHAR(512) DEFAULT ''")
                )
            sync_conn.execute(text("UPDATE profiles SET exclude_keywords = '' WHERE exclude_keywords IS NULL"))

        await conn.run_sync(run)
