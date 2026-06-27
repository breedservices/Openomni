from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING

from discord import Colour, SeparatorSpacing, file, interactions
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, MediaGallery, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot

ModelChoices = [
    Choice(name="DeepAI", value="deepai/image"),
    Choice(name="Opera Aria", value="opera/aria"),
]


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


async def _FetchImage(Url: str) -> tuple[bytes, str]:
    import aiohttp

    ExtMap = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    async with aiohttp.ClientSession() as Session:
        async with Session.get(Url) as Resp:
            Data = await Resp.read()
            ContentType = Resp.headers.get("Content-Type", "image/png")
            Ext = ExtMap.get(ContentType, "png")
            return Data, Ext


class Image(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot
        self._Client = None

    async def _GetClient(self):
        if self._Client is None:
            from fishr import AsyncClient

            self._Client = AsyncClient()
        return self._Client

    async def _Generate(self, Client, Prompt: str, Model: str) -> str | None:
        if Model == "opera/aria":
            Result = await Client.opera.ask_async(f"Generate an image of: {Prompt}")
            if Result.image_urls:
                return Result.image_urls[0]
            return None

        Result = await Client.images.generate(
            model=Model,
            prompt=Prompt,
        )
        if Result.data and Result.data[0].url:
            return Result.data[0].url
        return None

    @command(
        name="image",
        description="Generate an image from text",
    )
    @choices(model=ModelChoices)
    @describe(
        prompt="Image to generate",
        model="Model to use",
    )
    async def ImageCommand(
        self,
        Interaction: interactions.Interaction,
        prompt: str,
        model: str = "deepai/image",
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()
        Client = await self._GetClient()

        Url = await self._Generate(Client, prompt, model)
        if not Url:
            await Interaction.followup.send(content="image generation failed")
            return

        Data, Ext = await _FetchImage(Url)
        from io import BytesIO
        from random import randint

        Filename = f"image.{Ext}"
        ImageFile = file.File(BytesIO(Data), filename=Filename)
        Elapsed = _FormatElapsed((monotonic() - Start) * 1000)
        UserMention = Interaction.user.mention if Interaction.user else "Unknown"

        View = LayoutView()
        View.add_item(
            Container(
                TextDisplay(content=f"Prompt: {prompt}\nModel: {model}\n"),
                MediaGallery().add_item(media=f"attachment://{Filename}"),
                Separator(
                    visible=True,
                    spacing=SeparatorSpacing.small,
                ),
                TextDisplay(content=f"time taken {Elapsed} • invoked by {UserMention}"),
                accent_colour=Colour(randint(0, 0xFFFFFF)),
            )
        )

        await Interaction.followup.send(file=ImageFile, view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Image(Bot))
