from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING

from discord import Colour, SeparatorSpacing, interactions
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot

GlmChoices = {
    "telnyx/glm-5.2": "GLM 5.2",
    "telnyx/glm-5.1": "GLM 5.1",
}

GlmChoiceList = [Choice(name=Name, value=Value) for Value, Name in GlmChoices.items()]


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


class Glm(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot
        self._Client = None

    async def _GetClient(self):
        if self._Client is None:
            from fishr import AsyncClient

            self._Client = AsyncClient()
        return self._Client

    @command(
        name="glm",
        description="ask GLM a question",
    )
    @choices(model=GlmChoiceList)
    @describe(
        prompt="Your message",
        model="GLM model to use",
        thinking="Enable thinking/reasoning mode",
    )
    async def GlmCommand(
        self,
        Interaction: interactions.Interaction,
        prompt: str,
        model: str = "telnyx/glm-5.1",
        thinking: bool = False,
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()
        Client = await self._GetClient()

        Result = await Client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            think_harder=thinking,
        )
        Content = Result.text
        if not Content:
            await Interaction.followup.send(content="glm returned no response :(")
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
                    content=f"{GlmChoices[model]} • time taken {Elapsed} • invoked by {UserMention}"
                ),
                accent_colour=Colour(randint(0, 0xFFFFFF)),
            )
        )

        await Interaction.followup.send(view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Glm(Bot))
