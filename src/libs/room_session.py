from dataclasses import dataclass
from typing import List

import discord


@dataclass
class RoomSession:
    guild: discord.Guild
    main_voice_channel: discord.VoiceChannel
    voice_channels: List[discord.VoiceChannel]
