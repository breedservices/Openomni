from __future__ import annotations

from base64 import b64encode
from time import monotonic
from typing import TYPE_CHECKING

from discord import Colour, SeparatorSpacing, file, flags, http, interactions
from discord.app_commands import Choice, choices, command, describe
from discord.ext.commands import Cog
from discord.ui import Container, LayoutView, Separator, TextDisplay

if TYPE_CHECKING:
    from discord.ext.commands import Bot

TelnyxVoices = (
    "astra",
    "luna",
    "sol",
    "nova",
    "orion",
)

VoiceChoices = [
    Choice(
        name=Voice.capitalize(),
        value=Voice,
    )
    for Voice in TelnyxVoices
]

ModeChoices = [
    Choice(name="File", value="file"),
    Choice(name="Voice Message", value="voice"),
]

MimeExt = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/opus": "ogg",
}


def ResolveExt(Mime: str) -> str:
    return MimeExt.get(Mime, "mp3")


def _Waveform(Audio: bytes, Bars: int = 16) -> str:
    Step = max(1, len(Audio) // Bars)
    Peaks = []
    for I in range(Bars):
        Chunk = Audio[I * Step : (I + 1) * Step]
        Peak = max(abs(B) for B in Chunk) if Chunk else 0
        Peaks.append(Peak)
    MaxPeak = max(Peaks) if Peaks else 1
    if MaxPeak == 0:
        MaxPeak = 1
    Normalized = bytes(min(255, int(P / MaxPeak * 255)) for P in Peaks)
    return b64encode(Normalized).decode()


def _Duration(Audio: bytes) -> float:
    Bitrate = 64000
    return len(Audio) * 8 / Bitrate


def _FormatElapsed(Ms: float) -> str:
    if Ms >= 1000:
        return f"{Ms / 1000:.1f}s"
    return f"{Ms:.0f}ms"


def _BuildContainer(
    Prompt: str, Voice: str, Elapsed: str, UserMention: str
) -> LayoutView:
    from random import randint

    View = LayoutView()
    View.add_item(
        Container(
            TextDisplay(content=f"Prompt: {Prompt}\nVoice: {Voice}\n"),
            Separator(
                visible=True,
                spacing=SeparatorSpacing.small,
            ),
            TextDisplay(content=f"time taken {Elapsed} • invoked by {UserMention}"),
            accent_colour=Colour(randint(0, 0xFFFFFF)),
        )
    )
    return View


class Tts(Cog):
    def __init__(self, Bot: "Bot") -> None:
        self.Bot = Bot
        self._Client = None

    async def _GetClient(self):
        if self._Client is None:
            from fishr import AsyncClient

            self._Client = AsyncClient()
        return self._Client

    async def _SendVoiceMsg(
        self,
        Interaction: interactions.Interaction,
        Audio: bytes,
    ) -> None:
        from io import BytesIO

        from discord.utils import _to_json

        Filename = "voice-message.ogg"
        AudioFile = file.File(BytesIO(Audio), filename=Filename)
        Payload = {
            "flags": 8192,
            "attachments": [
                {
                    "id": "0",
                    "filename": Filename,
                    "duration_secs": round(_Duration(Audio), 2),
                    "waveform": _Waveform(Audio),
                }
            ],
        }
        Form = [
            {
                "name": "payload_json",
                "value": _to_json(Payload),
                "content_type": "application/json",
            },
            {
                "name": "files[0]",
                "value": Audio,
                "filename": Filename,
                "content_type": "application/octet-stream",
            },
        ]
        Route_ = http.Route(
            "POST",
            "/webhooks/{webhook_id}/{webhook_token}",
            webhook_id=Interaction.application_id,
            webhook_token=Interaction.token,
        )
        await Interaction.client.http.request(
            Route_,
            files=[AudioFile],
            form=Form,
        )

    @command(
        name="tts",
        description="Convert text to speech",
    )
    @choices(voice=VoiceChoices, mode=ModeChoices)
    @describe(
        prompt="Text to convert to speech",
        voice="Voice to use",
        mode="Send as file or voice message",
    )
    async def TtsCommand(
        self,
        Interaction: interactions.Interaction,
        prompt: str,
        voice: str = "astra",
        mode: str = "file",
    ) -> None:
        Start = monotonic()
        await Interaction.response.defer()
        Client = await self._GetClient()
        Response = await Client.audio.speech.create(
            model=f"telnyx-tts/{voice}",
            input=prompt,
            voice=voice,
        )
        if not Response.data or not Response.data[0].audio:
            await Interaction.followup.send(content="tts failed")
            return

        Audio = Response.data[0].audio
        SourceMime = Response.data[0].mime_type

        if mode == "voice":
            from fishr.audio.Transcode import Transcode

            Result = Transcode(Audio, "opus", SourceMime=SourceMime)
            if Result is not None:
                Audio, _ = Result
            await self._SendVoiceMsg(Interaction, Audio)
        else:
            from io import BytesIO

            Ext = ResolveExt(SourceMime)
            AudioFile = file.File(BytesIO(Audio), filename=f"tts.{Ext}")
            await Interaction.followup.send(file=AudioFile)

        Elapsed = _FormatElapsed((monotonic() - Start) * 1000)
        UserMention = Interaction.user.mention if Interaction.user else "Unknown"
        View = _BuildContainer(prompt, voice, Elapsed, UserMention)
        await Interaction.followup.send(view=View)


async def setup(Bot: "Bot") -> None:
    await Bot.add_cog(Tts(Bot))
