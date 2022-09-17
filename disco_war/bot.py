from io import BytesIO

import discord

from disco_war.processing import ReplayFileProcessing, AttachmentProcessingResult


class SurvivalChaosClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        processing = AttachmentProcessing()
        for attachment in message.attachments:
            result = await processing.process(attachment)
            if result is None:
                return
            await message.channel.send(result.formatted())


class AttachmentProcessing:
    def __init__(self):
        self.file_processing = ReplayFileProcessing()

    async def process(self, attachment: discord.Attachment) -> AttachmentProcessingResult | None:
        if '.w3g' not in attachment.filename:
            return None
        file = BytesIO(await attachment.read())
        return await self.file_processing.process(file)
