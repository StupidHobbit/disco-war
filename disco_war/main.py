import os

import discord

from disco_war.bot import SurvivalChaosClient


def main():
    intents = discord.Intents.default()
    intents.message_content = True

    client = SurvivalChaosClient(intents=intents)
    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
