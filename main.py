from __future__ import annotations

from pathlib import Path

from discord import AllowedMentions, Intents, MemberCacheFlags
from discord.app_commands import AppCommandContext
from discord.ext.commands import Bot
from fishr.Loop import asyncio as nigga

from config import LoadConfig
from Log import SetupLog

Log = SetupLog()

CogDir = Path(__file__).parent / "commands"


def DiscoverCogs() -> tuple[str, ...]:
    return tuple(
        f"commands.{File.stem}"
        for File in CogDir.glob("*.py")
        if not File.stem.startswith("_") and File.stem != "shared"
    )


class Omni(Bot):
    async def setup_hook(self) -> None:
        Cogs = DiscoverCogs()
        for Cog in Cogs:
            await self.load_extension(Cog)
        Synced = await self.tree.sync()
        Log.info("synced %d commands", len(Synced))

    async def on_ready(self) -> None:
        if self.user is not None:
            Log.info("logged in as %s", self.user)


async def Main() -> None:
    Cfg = LoadConfig("cfg.json")
    Bot = Omni(
        command_prefix="!",
        intents=Intents.default(),
        member_cache_flags=MemberCacheFlags.none(),
        chunk_guilds_at_startup=False,
        allowed_mentions=AllowedMentions.none(),
        allowed_contexts=AppCommandContext(
            guild=True,
            dm_channel=True,
            private_channel=True,
        ),
    )
    await Bot.start(Cfg.Token)


if __name__ == "__main__":
    nigga.run(Main())
