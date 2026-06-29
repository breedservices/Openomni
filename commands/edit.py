from __future__ import annotations

from base64 import b64encode
from time import monotonic
from typing import TYPE_CHECKING

from discord import Attachment, Colour, SeparatorSpacing, file, interactions
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, MediaGallery, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot

AspectChoices = [
    Choice(name="Auto", value="auto"),
    Choice(name="Square (1:1)", value="1:1"),
    Choice(name="Portrait (9:16)", value="9:16"),
    Choice(name="Landscape (16:9)", value="16:9"),
]

ResolutionChoices = [
    Choice(name="1K", value="1k"),
    Choice(name="2K", value="2k"),
]

MimeExt = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/jpg": "jpg",
}


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


async def _FetchImage(Url: str) -> tuple[bytes, str]:
    ExtMap = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
    }
    from .shared import GetSession

    Session = await GetSession()
    async with Session.get(Url) as Resp:
        Data = await Resp.read()
        ContentType = Resp.headers.get("Content-Type", "image/png")
        Ext = ExtMap.get(ContentType, "png")
        return Data, Ext


class Edit(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot

    async def _GetClient(self):
        from .shared import GetClient

        return await GetClient()

    @command(
        name="edit",
        description="Edit an image using AI",
    )
    @choices(aspect=AspectChoices, resolution=ResolutionChoices)
    @describe(
        prompt="How to edit the image",
        image="Image to edit",
        aspect="Output aspect ratio",
        resolution="Output resolution",
    )
    async def EditCommand(
        self,
        Interaction: interactions.Interaction,
        prompt: str,
        image: Attachment,
        aspect: str = "auto",
        resolution: str = "1k",
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()

        ContentType = image.content_type or "image/png"
        Mime = ContentType.split(";")[0].strip()
        if Mime not in MimeExt:
            await Interaction.followup.send(content="unsupported image format")
            return

        ImgData = await image.read()
        Encoded = b64encode(ImgData).decode()

        Client = await self._GetClient()
        Result = await Client.images.generate(
            model="raphael/image",
            prompt=prompt,
            image={
                "mime_type": Mime,
                "base64_data": Encoded,
            },
            aspect=aspect,
            resolution=resolution,
        )

        if not Result.data or not Result.data[0].url:
            await Interaction.followup.send(content="image edit failed")
            return

        Data, Ext = await _FetchImage(Result.data[0].url)
        from io import BytesIO
        from random import randint

        Filename = f"edited.{Ext}"
        ImageFile = file.File(BytesIO(Data), filename=Filename)
        Elapsed = _FormatElapsed((monotonic() - Start) * 1000)
        UserMention = Interaction.user.mention if Interaction.user else "Unknown"

        View = LayoutView()
        View.add_item(
            Container(
                TextDisplay(content=f"Prompt: {prompt}\n"),
                MediaGallery().add_item(media=f"attachment://{Filename}"),
                Separator(
                    visible=True,
                    spacing=SeparatorSpacing.small,
                ),
                TextDisplay(
                    content=f"Raphael • time taken {Elapsed} • invoked by {UserMention}"
                ),
                accent_colour=Colour(randint(0, 0xFFFFFF)),
            )
        )

        await Interaction.followup.send(file=ImageFile, view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Edit(Bot))
