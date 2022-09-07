from dotenv import load_dotenv
from discord.ui import Button, View
from typing import Callable, Coroutine
from asyncio import Lock
from PIL import Image
import discord
import os

from io_abc import IO
from game import CoupGame, Player

load_dotenv()

TOKEN =                     os.getenv('TOKEN')
COUP_SERVER_ID =            int(os.getenv('COUP_SERVER_ID'))
COUP_CHANNEL_ID =           int(os.getenv('COUP_CHANNEL_ID'))
COUP_CHANNEL_NAME =         os.getenv('COUP_CHANNEL_NAME')
LOBBY_CHANNEL_ID =          int(os.getenv('LOBBY_CHANNEL_ID'))
LOBBY_CHANNEL_NAME =        os.getenv('LOBBY_CHANNEL_NAME')
ADMIN_ID =                  int(os.getenv('ADMIN_ID'))

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True


class dClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False


client = dClient()
tree = discord.app_commands.CommandTree(client)
EMBED_GAME_COLOR = 0x0000FF
EMBED_MISC_COLOR = 0x00FF00
EMBED_ERROR_COLOR = 0xFF0000

playerQueue = []
playerQueueLock: Lock = Lock()
"""To prevent race conditions, this should be used whenever playerQueue is 
changed/used."""

cardPicNames = {
    "Ambassador": "o6HpGwo",
    "AmbassadorAmbassador": "iGVRrdm",
    "AmbassadorAssassin": "Ip4E0Ez",
    "AmbassadorCaptain": "mrgoO41",
    "AmbassadorContessa": "LFQRKKw",
    "AmbassadorDuke": "b9dohPG",
    "Assassin": "jKJQdRP",
    "AssassinAssassin": "MACYQBq",
    "AssassinCaptain": "GJGl4ov",
    "AssassinContessa": "FuVrV3s",
    "AssassinDuke": "ixJO0ZN",
    "Captain": "T61eAPB",
    "CaptainCaptain": "JhvbshV",
    "CaptainContessa": "P9TnJeK",
    "CaptainDuke": "XQOzsz2",
    "Contessa": "FcJLtTI",
    "ContessaContessa": "jAHEYdp",
    "ContessaDuke": "Z55Q9vc",
    "Duke": "8DxkXvM",
    "DukeDuke": "AXREh1r"
}

coupCommands = {

}
"""All commands currently available for public use. Each is associated with the
channel that it must be used in and a brief description."""

with open("rules.txt", "r") as file:
    coupRules = file.read()


def getCardImageURL(cardCombination: str) -> str:
    """
    :param cardCombination: E.g. AssassinContessa
    :returns: URL to be used in embeds.
    """
    return f"https://i.imgur.com/{cardPicNames[cardCombination]}.png"


def getDefaultGameEmbed(title: str, description: str = None) -> discord.Embed:
    """
    :returns: Embed for the main game."""
    return discord.Embed(
        title = title,
        description = description,
        color = EMBED_GAME_COLOR
    )


def getDefaultMiscEmbed(title: str, description: str = None) -> discord.Embed:
    """
    :returns: Embed for miscellaneous messages."""
    return discord.Embed(
        title = title,
        description = description,
        color = EMBED_MISC_COLOR
    )


def getDefaultErrorEmbed(title: str, description: str = None) -> discord.Embed:
    """
    :returns: Embed for error messages."""
    return discord.Embed(
        title = title,
        description = description,
        color = EMBED_ERROR_COLOR
    )


# class CoupBotIO(IO):
#     """Defines I/O methods for Coup that is played in Discord."""
#     async def displayMessage(self, message: str):
#         await COUP_CHANNEL.send(embed = getDefaultGameEmbed(message))
#
#     async def displayError(self, message: str):
#         await COUP_CHANNEL.send(embed = getDefaultErrorEmbed(message))
#
#     async def displayStatus(self, message: str):
#         await COUP_CHANNEL.send(embed = getDefaultMiscEmbed(message))
#
#     async def displayEmbed(self, embed: discord.Embed, view: View = None):
#         if view:
#             await COUP_CHANNEL.send(embed = embed, view = view)
#         else:
#             await COUP_CHANNEL.send(embed = embed)


@client.event
async def on_ready():
    await client.wait_until_ready()

    global COUP_SERVER
    global COUP_CHANNEL
    global LOBBY_CHANNEL
    COUP_SERVER = client.get_guild(COUP_SERVER_ID)
    COUP_CHANNEL = client.get_channel(COUP_CHANNEL_ID)
    LOBBY_CHANNEL = client.get_channel(LOBBY_CHANNEL_ID)

    if not client.synced:
        await tree.sync(guild = discord.Object(id = COUP_SERVER_ID))
        client.synced = True

    global currentGame
    currentGame = None

    print("Coup bot has logged in.")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.guild:
        try:
            if message.content == "!shutdown" and message.author.id == ADMIN_ID:
                await message.channel.send("Shutting down")
                await client.close()
        except discord.errors.Forbidden:
            pass
        return

    if message.content == ".img":
        embed = discord.Embed(title = "Title", description = "Desc", color = EMBED_MISC_COLOR)
        file2 = discord.File("./card-images/AmbassadorAssassin.png", filename = "ambassador.png")
        embed.set_image(url="https://i.imgur.com/iQOFAZz.png")
        await message.channel.send(embed=embed)

    if message.content in cardPicNames.keys():
        embed = discord.Embed(title = "Title", description = "Desc", color = EMBED_MISC_COLOR)
        embed.set_image(url = getCardImageURL(message.content))
        await message.channel.send(embed = embed)


async def usedInAcceptedChannel(interaction: discord.Interaction,
                                acceptedChannelId: int, acceptedChannelName: str) -> bool:
    """Call within a slash command. Responds to interaction if the channel that
    the interaction is called from is not the accepted one.

    :param interaction: Interaction to respond to.
    :param acceptedChannelId: id of the channel that the slash command should be
        called from.
    :param acceptedChannelName: Name of the channel that the slash command
        should be called from
    :returns: Whether the interaction was called from the accepted channel."""
    if interaction.channel_id != acceptedChannelId:
        await interaction.response.send_message(
            embed = getDefaultErrorEmbed(f"This command can only be used in the `{acceptedChannelName}` channel."),
            ephemeral = True
        )
        return False
    return True


client.run(TOKEN)
