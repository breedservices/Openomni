from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING

from discord import Colour, SeparatorSpacing, interactions
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


class Qwen(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot
        self._Client = None

    async def _GetClient(self):
        if self._Client is None:
            from fishr import AsyncClient

            self._Client = AsyncClient()
        return self._Client

    @command(
        name="qwen",
        description="Chat with Qwen",
    )
    @describe(
        prompt="Your message",
        web_search="Enable web search",
    )
    async def QwenCommand(
        self,
        Interaction: interactions.Interaction,
        prompt: str,
        web_search: bool = False,
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()
        Client = await self._GetClient()

        Result = await Client.chat.completions.create(
            model="noxus/qwen",
            messages=[{"role": "user", "content": prompt}],
            web_search=web_search,
        )
        Content = Result.text
        if not Content:
            await Interaction.followup.send(content="qwen returned no response")
            return

        Elapsed = _FormatElapsed((monotonic() - Start) * 1000)
        UserMention = Interaction.user.mention if Interaction.user else "Unknown"

        from random import randint

        View = LayoutView()
        View.add_item(
            Container(
                TextDisplay(content=Content),
                Separator(
                    visible=True,
                    spacing=SeparatorSpacing.small,
                ),
                TextDisplay(
                    content=f"Qwen • time taken {Elapsed} • invoked by {UserMention}"
                ),
                accent_colour=Colour(randint(0, 0xFFFFFF)),
            )
        )

        await Interaction.followup.send(view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Qwen(Bot))
