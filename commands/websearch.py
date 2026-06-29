from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING

from discord import Colour, SeparatorSpacing, interactions
from discord.app_commands import command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


async def _Search(Query: str, MaxResults: int = 12) -> list[dict]:
    from ddgs import DDGS
    from fishr.Loop import asyncio

    def _Run():
        return DDGS().text(Query, max_results=MaxResults)

    return await asyncio.to_thread(_Run)


class Websearch(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot

    async def _GetClient(self):
        from .shared import GetClient

        return await GetClient()

    @command(
        name="websearch",
        description="Search the web and get results",
    )
    @describe(query="What to search for")
    async def WebsearchCommand(
        self,
        Interaction: interactions.Interaction,
        query: str,
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()

        Results = await _Search(query)
        if not Results:
            await Interaction.followup.send(content="no results found")
            return

        Context = "\n\n".join(
            f"**{R['title']}**\n{R['href']}\n{R['body']}" for R in Results
        )
        System = (
            "You are a web search assistant. Using the provided search results, "
            "write a clear, well-structured answer to the user's query. "
            "Cite sources by including the URL inline where relevant. "
            "Do not make up information not present in the results."
        )
        Client = await self._GetClient()
        Result = await Client.chat.completions.create(
            model="telnyx/glm-5.1",
            messages=[
                {"role": "system", "content": System},
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nSearch Results:\n{Context}",
                },
            ],
        )
        Content = Result.text
        if not Content:
            await Interaction.followup.send(content="websearch returned no response")
            return

        ContentMaxLen = 4000
        if len(Content) > ContentMaxLen:
            Content = Content[:ContentMaxLen] + "..."

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
                    content=f"Websearch • time taken {Elapsed} • invoked by {UserMention}"
                ),
                accent_colour=Colour(randint(0, 0xFFFFFF)),
            )
        )

        await Interaction.followup.send(view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Websearch(Bot))
