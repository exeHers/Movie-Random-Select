from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


def _sqlite_schema_patches(sync_conn) -> None:
    rows = sync_conn.execute(text("PRAGMA table_info(profiles)")).fetchall()
    cols = {row[1] for row in rows}
    if "rotation_order" not in cols:
        sync_conn.execute(text("ALTER TABLE profiles ADD COLUMN rotation_order INTEGER"))
    if "exclude_keywords" not in cols:
        sync_conn.execute(
            text("ALTER TABLE profiles ADD COLUMN exclude_keywords VARCHAR(512) DEFAULT ''")
        )
    sync_conn.execute(text("UPDATE profiles SET exclude_keywords = '' WHERE exclude_keywords IS NULL"))


async def run_migrations(engine: AsyncEngine) -> None:
    url = str(engine.url)
    async with engine.begin() as conn:
        # Rename legacy rotation slugs (stepdad/you → dad/son) for existing DBs.
        await conn.execute(
            text(
                "UPDATE profiles SET slug = 'dad', display_name = 'Dad' "
                "WHERE slug = 'stepdad'"
            )
        )
        await conn.execute(text("UPDATE profiles SET display_name = 'Mom' WHERE slug = 'mom'"))
        await conn.execute(
            text(
                "UPDATE profiles SET slug = 'son', display_name = 'Son' "
                "WHERE slug = 'you'"
            )
        )
        if url.startswith("sqlite"):
            await conn.run_sync(_sqlite_schema_patches)
