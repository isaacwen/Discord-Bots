from dotenv import load_dotenv
from discord.ui import Button, View
from typing import Callable, Coroutine
from asyncio import Lock
import discord
import os

from io_abc import IO
from game import UnoGame, Player, Card, PlayerMove, Color, Value, MAX_PLAYERS, MIN_PLAYERS, UNO_PENALTY

load_dotenv()

TOKEN =                     os.getenv('TOKEN')
UNO_SERVER_ID =             int(os.getenv('UNO_SERVER_ID'))
UNO_CHANNEL_ID =            int(os.getenv('UNO_CHANNEL_ID'))
UNO_CHANNEL_NAME =          os.getenv('UNO_CHANNEL_NAME')
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

unoCommands = {
    "commands": [LOBBY_CHANNEL_NAME, "View all commands"],
    "rules": [LOBBY_CHANNEL_NAME, "View rules"],
    "queue": [LOBBY_CHANNEL_NAME, "View the current queue"],
    "joinqueue": [LOBBY_CHANNEL_NAME, "Join the queue"],
    "leavequeue": [LOBBY_CHANNEL_NAME, "Leave the queue"],
    "startgame": [LOBBY_CHANNEL_NAME, "Start a game"],
    "hand": [UNO_CHANNEL_NAME, "View current hand"],
    "gamestate": [UNO_CHANNEL_NAME, "View current game state"],
    "uno": [UNO_CHANNEL_NAME, "Call 'Uno!'"]
}
"""All commands currently available for public use. Each is associated with the
channel that is must be used in and a brief description."""

with open("rules.txt", "r") as file:
    unoRules = file.read()

def convertCardToEmojiName(card: Card, addColons: bool = False) -> str:
    """Converts a card to its corresponding emoji name."""
    s = f"{card.color.name}_{card.value.name}"
    if addColons:
        s = ":" + s + ":"
    return s


def convertEmojiNameToExpandedEmoji(emojiName: str) -> str:
    """Converts a emoji to its expanded emoji format: <:EMOJI_NAME:EMOJI_ID>"""
    emojiId = discord.utils.get(UNO_SERVER.emojis, name = emojiName).id
    return f"<:{emojiName}:{emojiId}>"


def convertCardToExpandedEmoji(card: Card) -> str:
    """Converts a card to its expanded emoji format: <:EMOJI_NAME:EMOJI_ID>"""
    emojiName = convertCardToEmojiName(card)
    return convertEmojiNameToExpandedEmoji(emojiName)


def convertEmojiNameToEmojiURL(emojiName: str, size: int = 64) -> str:
    """Converts an emoji name (without colons) to its corresponding URL image."""
    emojiId: int = discord.utils.get(UNO_SERVER.emojis, name = emojiName).id
    return f"https://cdn.discordapp.com/emojis/{str(emojiId)}.png?size={str(size)}"


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


class ConfirmationButtons:
    def __init__(self,
                 curPlayer: Player,
                 # Declares async function as parameter
                 onReject: Callable[[], Coroutine]):
        """
        :param onReject: async function that should be called if the 'No' button
            is pressed."""
        self.player = curPlayer
        self.onReject = onReject

        self.rejectButton = Button(
            label = "No",
            style = discord.ButtonStyle.gray,
            custom_id = "rejectButton"
        )
        self.confirmButton = Button(
            label = "Yes",
            style = discord.ButtonStyle.gray,
            custom_id = "confirmButton"
        )

        self.confirmationView = View(timeout = None)
        self.confirmationView.add_item(self.rejectButton)
        self.confirmationView.add_item(self.confirmButton)

        self.rejectButton.callback = self.rejectButtonCallback
        self.confirmButton.callback = self.confirmButtonCallback

    def makeConfirmationEmbed(self, message: str, imageUrl: str = None) -> discord.Embed:
        embedConfirmation = discord.Embed(title = message, color = EMBED_GAME_COLOR)
        if imageUrl:
            embedConfirmation.set_image(url = imageUrl)
        return embedConfirmation

    def getConfirmationView(self) -> discord.ui.View:
        return self.confirmationView

    async def confirmationButtonsResponse(self, button: Button, interaction: discord.Interaction) -> bool:
        correctUser: bool = False
        if interaction.user.id == self.player.name:
            self.rejectButton.disabled, self.confirmButton.disabled = True, True
            button.style = discord.ButtonStyle.blurple
            correctUser = True
        await interaction.response.edit_message(view = self.confirmationView)
        return correctUser

    def resetButtons(self):
        """Resets buttons."""
        self.rejectButton.disabled, self.confirmButton.disabled = False, False
        self.rejectButton.style = discord.ButtonStyle.gray
        self.confirmButton.style = discord.ButtonStyle.gray

    async def rejectButtonCallback(self, interaction: discord.Interaction):
        if await self.confirmationButtonsResponse(self.rejectButton, interaction):
            self.resetButtons()
            await self.onReject()

    async def confirmButtonCallback(self, interaction: discord.Interaction):
        await self.confirmationButtonsResponse(self.confirmButton, interaction)


class DiscordBotIO(IO):
    """Defines I/O methods for Uno that is played in Discord."""
    async def displayMessage(self, message: str):
        await UNO_CHANNEL.send(embed = getDefaultGameEmbed(message))

    async def displayError(self, message: str):
        await UNO_CHANNEL.send(embed = getDefaultErrorEmbed(message))

    async def displayStatus(self, message: str):
        await UNO_CHANNEL.send(embed = getDefaultMiscEmbed(message))

    async def displayEmbed(self, embed: discord.Embed, view: View = None):
        if view:
            await UNO_CHANNEL.send(embed = embed, view = view)
        else:
            await UNO_CHANNEL.send(embed = embed)

    async def getInput(self, player: Player = None) -> str:
        def check(message: discord.Message):
            return message.author.id == player.name
        msg: discord.Message = await client.wait_for("message", check = check)
        return msg.content

    async def getPlayerInput(self, player: Player, topDiscard: Card, numDraw) -> (PlayerMove, int):
        """Input for what a player wants to do on a turn.

        HANDLES INVALID INPUT - DOES NOT THROW ERROR."""

        command: int
        n: int = 0

        p = await client.fetch_user(player.name)
        embedPlayerInput = discord.Embed(
            title = f"{p.display_name}, it is your turn.",
            description = "Select the move you would like to make. The current top card is:",
            color = EMBED_GAME_COLOR
        )
        embedPlayerInput.set_image(url = convertEmojiNameToEmojiURL(convertCardToEmojiName(topDiscard)))
        footer: str = ""
        cardValue: str = "+2" if topDiscard.value is Value.drawTwo else "+4"
        if numDraw:
            footer += "This card is active, meaning that you can only chain cards"
            footer += f" of the same value ({cardValue}), or you will draw "
            footer += f"{numDraw} cards if you choose to draw this turn."
        elif topDiscard.color is Color.black:
            footer += f"The chosen color of this card is {topDiscard.discardColor.name}."

        if footer:
            embedPlayerInput.set_footer(
                text = footer
            )

        defStyle: discord.ButtonStyle = discord.ButtonStyle.gray
        playButton = Button(label = "Play a card", style = defStyle, custom_id = "playButton")
        drawButton = Button(label = "Draw card(s)", style = defStyle, custom_id = "drawButton")
        quitButton = Button(label = "Quit game", style = defStyle, custom_id = "quitButton")

        playerInputView = View(timeout = None)
        playerInputView.add_item(playButton)
        playerInputView.add_item(drawButton)
        playerInputView.add_item(quitButton)

        async def playerInputButtonsResponse(button: Button, interaction: discord.Interaction) -> bool:
            """Returns whether the user who clicked the button is the player."""
            correctUser: bool = False
            if interaction.user.id == player.name:
                playButton.disabled, drawButton.disabled, quitButton.disabled = True, True, True
                button.style = discord.ButtonStyle.blurple
                correctUser = True
            await interaction.response.edit_message(view = playerInputView)
            return correctUser

        async def resetButtonsAndAskAgain():
            playButton.disabled, drawButton.disabled, quitButton.disabled = False, False, False
            playButton.style = discord.ButtonStyle.gray
            drawButton.style = discord.ButtonStyle.gray
            quitButton.style = discord.ButtonStyle.gray
            await self.displayEmbed(embedPlayerInput, playerInputView)

        confirmationButtons = ConfirmationButtons(player, resetButtonsAndAskAgain)

        async def playButtonCallback(interaction):
            if await playerInputButtonsResponse(playButton, interaction):
                nonlocal n
                nonlocal command
                s3 = "What card would you like to play? Respond with the "
                s3 += "corresponding emoji."
                await self.displayEmbed(getDefaultGameEmbed(s3))
                # Emojis read in will also have format <:EMOJI_NAME:EMOJI_ID>
                chosenCard: str = await self.getInput(player)
                try:
                    chosenCard = (chosenCard.split(":"))[1]
                    chosenColor, chosenValue = chosenCard.split("_")
                    cardInHand: bool = False
                    m: int = 0
                    for card in player.hand:
                        if card.correctColorValue(chosenColor, chosenValue):
                            cardInHand = True
                            break
                        m += 1
                    if not cardInHand:
                        await self.displayEmbed(
                            embed = getDefaultErrorEmbed("The card that you selected was not in your hand.")
                        )
                        await resetButtonsAndAskAgain()
                    else:
                        command = 0
                        n = m
                        s = "Are you sure you want to play the following card:"
                        await self.displayEmbed(
                            confirmationButtons.makeConfirmationEmbed(s, convertEmojiNameToEmojiURL(chosenCard)),
                            confirmationButtons.getConfirmationView()
                        )
                except:
                    await self.displayEmbed(
                        embed = getDefaultErrorEmbed("Invalid input.")
                    )
                    await resetButtonsAndAskAgain()

        async def drawButtonCallback(interaction):
            if await playerInputButtonsResponse(drawButton, interaction):
                nonlocal command
                command = 1
                s = "Are you sure that you want to draw card(s)?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        async def quitButtonCallback(interaction):
            if await playerInputButtonsResponse(quitButton, interaction):
                nonlocal command
                command = 2
                s = "Are you sure that you want to quit the game?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        playButton.callback = playButtonCallback
        drawButton.callback = drawButtonCallback
        quitButton.callback = quitButtonCallback

        await self.displayEmbed(embed = embedPlayerInput, view = playerInputView)

        # Only continue after the confirm button has been pressed
        def confirmButtonPressedCheck(interaction: discord.Interaction):
            if interaction.user.id != player.name:
                return False
            try:
                return interaction.data["custom_id"] == "confirmButton"
            except KeyError:
                return False

        await client.wait_for("interaction", check = confirmButtonPressedCheck)

        return PlayerMove(command), n

        # command: int
        # n: int = 0
        #
        # # s1 = "The top card is currently"
        # # if topDiscard.color is Color.black:
        # #     s1 += f" (note that the chosen color of this card is **{topDiscard.discardColor.name}**)"
        # # await self.displayMessage(s1)
        # # await self.displayMessage(discord.utils.get(UNO_SERVER.emojis, name = convertCardToEmoji(topDiscard)))
        # # s2 = f"<@{player.name}> it is your turn. Enter the command for the move "
        # # s2 += "you would like to make:\n`!play` to play a card.\n`!draw` to draw"
        # # s2 += " a card.\n`!quit` to quit the game."
        #
        # p = await client.fetch_user(player.name)
        # embedPlayerInput = discord.Embed(
        #     title = f"{p.display_name} it is your turn.",
        #     description = "Select the move you would like to make. The current top card is:",
        #     color = EMBED_GAME_COLOR
        # )
        # embedPlayerInput.set_image(url = convertEmojiNameToEmojiURL(convertCardToEmojiName(topDiscard)))
        # if topDiscard.color is Color.black:
        #     embedPlayerInput.set_footer(
        #         text = f"The chosen color of this card is {topDiscard.discardColor.name}."
        #     )
        #
        # def makeConfirmationEmbed(message: str, imageUrl: str = None) -> discord.Embed:
        #     embedConfirmation = discord.Embed(title = message, color = EMBED_GAME_COLOR)
        #     if imageUrl:
        #         embedConfirmation.set_image(url = imageUrl)
        #     return embedConfirmation
        #
        # defStyle: discord.ButtonStyle = discord.ButtonStyle.gray
        # playButton = Button(label = "Play a card", style = defStyle, custom_id = "playButton")
        # drawButton = Button(label = "Draw card(s)", style = defStyle, custom_id = "drawButton")
        # quitButton = Button(label = "Quit game", style = defStyle, custom_id = "quitButton")
        #
        # playerInputView = View()
        # playerInputView.add_item(playButton)
        # playerInputView.add_item(drawButton)
        # playerInputView.add_item(quitButton)
        #
        # rejectButton = Button(label = "No", style = defStyle, custom_id = "rejectButton")
        # confirmButton = Button(label = "Yes", style = defStyle, custom_id = "confirmButton")
        #
        # confirmationView = View()
        # confirmationView.add_item(rejectButton)
        # confirmationView.add_item(confirmButton)
        #
        # async def playerInputButtonsResponse(button: Button, interaction: discord.Interaction) -> bool:
        #     """Returns whether the user who clicked the button is the player."""
        #     correctUser: bool = False
        #     if interaction.user.id == player.name:
        #         playButton.disabled, drawButton.disabled, quitButton.disabled = True, True, True
        #         button.style = discord.ButtonStyle.blurple
        #         correctUser = True
        #     await interaction.response.edit_message(view = playerInputView)
        #     return correctUser
        #
        # async def confirmationButtonsResponse(button: Button, interaction: discord.Interaction) -> bool:
        #     correctUser: bool = False
        #     if interaction.user.id == player.name:
        #         rejectButton.disabled, confirmButton.disabled = True, True
        #         button.style = discord.ButtonStyle.blurple
        #         correctUser = True
        #     await interaction.response.edit_message(view = confirmationView)
        #     return correctUser
        #
        # async def resetButtonsAndAskAgain():
        #     playButton.disabled, drawButton.disabled, quitButton.disabled = False, False, False
        #     rejectButton.disabled, confirmButton.disabled = False, False
        #     playButton.style = discord.ButtonStyle.gray
        #     drawButton.style = discord.ButtonStyle.gray
        #     quitButton.style = discord.ButtonStyle.gray
        #     # Note that only the reject button style will ever need to be reset,
        #     # as if the user confirms the action there is no need to ask again.
        #     rejectButton.style = discord.ButtonStyle.gray
        #     await self.displayEmbed(embedPlayerInput, playerInputView)
        #
        # async def playButtonCallback(interaction):
        #     if await playerInputButtonsResponse(playButton, interaction):
        #         nonlocal n
        #         nonlocal command
        #         s3 = "What card would you like to play? Respond with the "
        #         s3 += "corresponding emoji."
        #         await self.displayEmbed(getDefaultGameEmbed(s3))
        #         # Emojis read in will also have format <:EMOJI_NAME:EMOJI_ID>
        #         chosenCard: str = await self.getInput(player)
        #         chosenCard = (chosenCard.split(":"))[1]
        #         chosenColor, chosenValue = chosenCard.split("_")
        #         cardInHand: bool = False
        #         m: int = 0
        #         for card in player.hand:
        #             if card.correctColorValue(chosenColor, chosenValue):
        #                 cardInHand = True
        #                 break
        #             m += 1
        #         if not cardInHand:
        #             await self.displayEmbed(
        #                 embed = getDefaultErrorEmbed("The card that you selected was not in your hand.")
        #             )
        #             await resetButtonsAndAskAgain()
        #         else:
        #             command = 0
        #             n = m
        #             s = "Are you sure you want to play the following card:"
        #             await self.displayEmbed(
        #                 makeConfirmationEmbed(s, convertEmojiNameToEmojiURL(chosenCard)),
        #                 confirmationView
        #             )
        #
        # async def drawButtonCallback(interaction):
        #     if await playerInputButtonsResponse(drawButton, interaction):
        #         nonlocal command
        #         command = 1
        #         s = "Are you sure that you want to draw card(s)?"
        #         await self.displayEmbed(makeConfirmationEmbed(s), confirmationView)
        #
        # async def quitButtonCallback(interaction):
        #     if await playerInputButtonsResponse(quitButton, interaction):
        #         nonlocal command
        #         command = 2
        #         s = "Are you sure that you want to quit the game?"
        #         await self.displayEmbed(makeConfirmationEmbed(s), confirmationView)
        #
        # async def rejectButtonCallback(interaction):
        #     if await confirmationButtonsResponse(rejectButton, interaction):
        #         await resetButtonsAndAskAgain()
        #
        # async def confirmButtonCallback(interaction):
        #     await confirmationButtonsResponse(confirmButton, interaction)
        #
        # playButton.callback = playButtonCallback
        # drawButton.callback = drawButtonCallback
        # quitButton.callback = quitButtonCallback
        #
        # rejectButton.callback = rejectButtonCallback
        # confirmButton.callback = confirmButtonCallback
        #
        # await self.displayEmbed(embed = embedPlayerInput, view = playerInputView)
        #
        # # Only continue after the confirm button has been pressed
        # def confirmButtonPressedCheck(interaction: discord.Interaction):
        #     if interaction.user.id != player.name:
        #         return False
        #     try:
        #         return interaction.data["custom_id"] == "confirmButton"
        #     except KeyError:
        #         return False
        #
        # await client.wait_for("interaction", check = confirmButtonPressedCheck)
        #
        # return PlayerMove(command), n
        # try:
        #     msg: str = await self.getInput(player)
        #     command: int
        #     n: int = 0
        #     match msg:
        #         case "!play":
        #             s3 = "What card would you like to play? Respond with the "
        #             s3 += "corresponding emoji."
        #             await self.displayMessage(s3)
        #             chosenCard: str = await self.getInput(player)
        #             chosenColor, chosenValue = chosenCard[1:-1].split("_")
        #             cardInHand: bool = False
        #             for card in player.hand:
        #                 if card.correctColorValue(chosenColor, chosenValue):
        #                     cardInHand = True
        #                     break
        #                 n += 1
        #             if not cardInHand:
        #                 raise ValueError()
        #             command = 0
        #         case "!draw":
        #             command = 1
        #         case "!quit":
        #             command = 2
        #         case _:
        #             raise ValueError()
        #     return PlayerMove(command), n
        # except:
        #     raise UnoError("Invalid input given when selecting move.")

    async def getPlayerColorChoice(self, player: Player) -> Color:
        """Input for what color a player wants when they play a black card.

        HANDLES INVALID INPUT - DOES NOT THROW ERRORS."""
        # s = f"<@{player.name}> what color would you like to choose? Enter the "
        # s += "command for the color you would like to choose: `!red`, `!blue`,"
        # s += " `!green`, or `!yellow`."

        c: Color = None

        p = await client.fetch_user(player.name)
        embedChooseColor = discord.Embed(
            title = f"{p.display_name}, what color would you like to choose?",
            color = EMBED_GAME_COLOR
        )

        defStyle: discord.ButtonStyle = discord.ButtonStyle.gray
        redButton = Button(label = "Red", style = defStyle, custom_id = "redButton")
        blueButton = Button(label = "Blue", style = defStyle, custom_id = "blueButton")
        greenButton = Button(label = "Green", style = defStyle, custom_id = "greenButton")
        yellowButton = Button(label = "Yellow", style = defStyle, custom_id = "yellowButton")

        chooseColorView = View(timeout = None)
        chooseColorView.add_item(redButton)
        chooseColorView.add_item(blueButton)
        chooseColorView.add_item(greenButton)
        chooseColorView.add_item(yellowButton)

        async def chooseColorButtonsResponse(button: Button, interaction: discord.Interaction):
            """Returns whether the user who clicked the button is the player."""
            correctUser: bool = False
            if interaction.user.id == player.name:
                redButton.disabled, blueButton.disabled = True, True
                greenButton.disabled, yellowButton.disabled = True, True
                button.style = discord.ButtonStyle.blurple
                correctUser = True
            await interaction.response.edit_message(view = chooseColorView)
            return correctUser

        async def resetButtonsAndAskAgain():
            redButton.disabled, blueButton.disabled = False, False
            greenButton.disabled, yellowButton.disabled = False, False
            redButton.style = discord.ButtonStyle.gray
            blueButton.style = discord.ButtonStyle.gray
            greenButton.style = discord.ButtonStyle.gray
            yellowButton.style = discord.ButtonStyle.gray
            await self.displayEmbed(embedChooseColor, chooseColorView)

        confirmationButtons = ConfirmationButtons(player, resetButtonsAndAskAgain)

        async def redButtonCallback(interaction):
            if await chooseColorButtonsResponse(redButton, interaction):
                nonlocal c
                c = Color(0)
                s = "Are you sure that you want to choose red?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        async def blueButtonCallback(interaction):
            if await chooseColorButtonsResponse(blueButton, interaction):
                nonlocal c
                c = Color(1)
                s = "Are you sure that you want to choose blue?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        async def greenButtonCallback(interaction):
            if await chooseColorButtonsResponse(greenButton, interaction):
                nonlocal c
                c = Color(2)
                s = "Are you sure that you want to choose green?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        async def yellowButtonCallback(interaction):
            if await chooseColorButtonsResponse(yellowButton, interaction):
                nonlocal c
                c = Color(3)
                s = "Are you sure that you want to choose yellow?"
                await self.displayEmbed(
                    confirmationButtons.makeConfirmationEmbed(s),
                    confirmationButtons.confirmationView
                )

        redButton.callback = redButtonCallback
        blueButton.callback = blueButtonCallback
        greenButton.callback = greenButtonCallback
        yellowButton.callback = yellowButtonCallback

        await self.displayEmbed(embed = embedChooseColor, view = chooseColorView)

        def confirmButtonPressedCheck(interaction: discord.Interaction):
            if interaction.user.id != player.name:
                return False
            try:
                return interaction.data["custom_id"] == "confirmButton"
            except KeyError:
                return False

        await client.wait_for("interaction", check = confirmButtonPressedCheck)

        return c

        # while not c:
        #     try:
        #         await self.displayMessage(s)
        #         colorChoice: str = await self.getInput(player)
        #         match colorChoice:
        #             case "!red":
        #                 c = Color(0)
        #             case "!blue":
        #                 c = Color(1)
        #             case "!green":
        #                 c = Color(2)
        #             case "!yellow":
        #                 c = Color(3)
        #             case _:
        #                 raise ValueError()
        #     except ValueError:
        #         await self.displayMessage("Invalid input when selecting a color.")
        # return c

    async def displayFirstValidDrawnCard(self, playerName, validCard, totalDrawn):
        embedDescription = "The following card is the first valid card in the "
        embedDescription += "deck, and it will be played for you:"
        if not validCard:
            await self.displayError("No cards remaining in deck.")
            embedDescription = "There are no valid cards remaining in the deck."

        player = await client.fetch_user(playerName)
        embed = discord.Embed(
            title = f"{player.display_name}, you have drawn {totalDrawn} card(s).",
            description = embedDescription,
            color = EMBED_GAME_COLOR
        )
        if validCard:
            embed.set_image(url = convertEmojiNameToEmojiURL(convertCardToEmojiName(validCard)))
        await self.displayEmbed(embed)

    async def playerWon(self, player: Player):
        p = await client.fetch_user(player.name)
        await self.displayEmbed(
            embed = getDefaultGameEmbed(f"{p.display_name} has just won the game!")
        )


@client.event
async def on_ready():
    await client.wait_until_ready()

    global UNO_SERVER
    global UNO_CHANNEL
    global LOBBY_CHANNEL_ID
    UNO_SERVER = client.get_guild(UNO_SERVER_ID)
    UNO_CHANNEL = client.get_channel(UNO_CHANNEL_ID)
    LOBBY_CHANNEL = client.get_channel(LOBBY_CHANNEL_ID)

    if not client.synced:
        await tree.sync(guild = discord.Object(id = UNO_SERVER_ID))
        client.synced = True

    global currentGame
    currentGame = None

    print(f"Uno Bot has logged in.")


# class customView(discord.ui.View):
#     def __init__(self, user):
#         self.user = user
#         super().__init__()
#
#     async def interaction_check(self, interaction: discord.Interaction) -> bool:
#         if interaction.user != self.user:
#             # TODO: remove this line
#             await UNO_CHANNEL.send("You don't have permission to press this button")
#             return False
#         return True


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


@tree.command(name = "hand", description = "Shows current hand.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if await usedInAcceptedChannel(interaction, UNO_CHANNEL_ID, UNO_CHANNEL_NAME):
        player: int = interaction.user.id
        if currentGame:
            await currentGame.acquirePlayerLock(f"Viewing player {player}'s hand.")
            try:
                s: str = "   "
                hand: list[Card] = currentGame.getPlayerHand(player)
                for card in hand:
                    s += convertCardToExpandedEmoji(card) + "   "
                await interaction.response.send_message(s, ephemeral = True)
            except Exception as e:
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed("There is not an active game/you aren't in the active game."),
                    ephemeral = True
                )
            finally:
                currentGame.releasePlayerLock(f"Finished viewing player {player}'s hand")
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is not an active game/you aren't in the active game."),
                ephemeral = True
            )


@tree.command(name = "gamestate", description = "Shows the number of cards in each player's hand.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if await usedInAcceptedChannel(interaction, UNO_CHANNEL_ID, UNO_CHANNEL_NAME):
        if currentGame:
            await currentGame.acquirePlayerLock("Viewing cards in each player's hands.")
            players: str = ""
            numCards: str = ""
            for player in currentGame.players:
                p = await client.fetch_user(player.name)
                players += p.display_name + "\n"
                numCards += str(player.handSize()) + "\n"
            currentGame.releasePlayerLock("Finished viewing cards in each player's hands.")

            turnOrder: int = currentGame.turnOrder
            arrowEmojiName: str
            if turnOrder == 1:
                arrowEmojiName = ":arrow_down:"
            else:
                arrowEmojiName = ":arrow_up:"

            embedGameState = discord.Embed(
                title = "Current Game State",
                color = EMBED_MISC_COLOR
            )
            embedGameState.add_field(name = "Player Name", value = players, inline = True)
            embedGameState.add_field(name = "Number of Cards", value = numCards, inline = True)
            embedGameState.add_field(name = "Turn Order", value = arrowEmojiName, inline = True)
            await interaction.response.send_message(embed = embedGameState)
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is not an active game.")
            )


@tree.command(name = "startgame", description = "Starts the Uno game.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    global playerQueue
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        if not currentGame:
            await playerQueueLock.acquire()
            if len(playerQueue) < MIN_PLAYERS:
                errorMessage = f"Unable to start game. {len(playerQueue)} out of a "
                errorMessage += f"minimum of {MIN_PLAYERS} players are in queue."
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed(errorMessage)
                )
                return
            frontQueue: list[int] = playerQueue[:MAX_PLAYERS]
            await interaction.response.send_message(
                embed = getDefaultMiscEmbed(
                    f"Starting Uno game with {len(frontQueue)} players.",
                    f"The maximum number of players in a game is {MAX_PLAYERS}."
                )
            )
            currentGame = UnoGame(playerQueue[:MAX_PLAYERS], DiscordBotIO())
            playerQueue = playerQueue[MAX_PLAYERS:]
            playerQueueLock.release()
            await currentGame.startGame()
            currentGame = None
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is already a game in progress.")
            )


@tree.command(name = "stopgame", description = "Stops the current game of Uno.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if interaction.user.id == ADMIN_ID:
        if currentGame:
            currentGame = None
            await interaction.response.send_message(
                embed = getDefaultGameEmbed("Game has been stopped.")
            )
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is no active game."),
                ephemeral = True
            )
    else:
        await interaction.response.send_message(
            embed = getDefaultErrorEmbed("You do not have permission to use this command."),
            ephemeral = True
        )


@tree.command(name = "joinqueue", description = "Joins queue for Uno.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    global playerQueue
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            player = interaction.user.id

            # Check that the user isn't in the current game.
            if currentGame:
                await currentGame.acquirePlayerLock(f"Checking if player {player} is in the current game.")
                if player in currentGame.playerNames:
                    await interaction.response.send_message(
                        embed = getDefaultErrorEmbed("You are already in the active game.")
                    )
                    currentGame.releasePlayerLock(f"Finished checking if player {player} is in the current game.")
                    return
                currentGame.releasePlayerLock(f"Finished checking if player {player} is in the current game.")

            if player in playerQueue:
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed("You are already in the queue.")
                )
            else:
                playerQueue.append(player)
                embedQueue = discord.Embed(
                    title = "You have been added to the queue for the next game of Uno.",
                    description = "Use `/queue` to view your position in queue.\nUse `/leavequeue` to leave the queue.",
                    color = EMBED_MISC_COLOR
                )
                await interaction.response.send_message(
                    embed = embedQueue
                )


@tree.command(name = "leavequeue", description = "Leaves queue for Uno.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global playerQueue
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            player = interaction.user.id
            if player in playerQueue:
                playerQueue.remove(player)
                await interaction.response.send_message(
                    embed = getDefaultMiscEmbed("You have been removed from the queue for Uno.")
                )
            else:
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed("You were not in the queue.")
                )


@tree.command(name = "queue", description = "View current queue for Uno.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global playerQueue
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            players: str = ""
            for player in playerQueue:
                p = await client.fetch_user(player)
                players += p.display_name + "\n"

            if not players:
                players = "There are no players in queue currently."

            embedQueue = discord.Embed(
                title = "Queue for Uno (in order)",
                description = players,
                color = EMBED_MISC_COLOR
            )
            await interaction.response.send_message(
                embed = embedQueue
            )


@tree.command(name = "uno", description = "Calls 'Uno!' in the current game of Uno.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if await usedInAcceptedChannel(interaction, UNO_CHANNEL_ID, UNO_CHANNEL_NAME):
        if currentGame:
            curPlayerId = interaction.user.id
            curPlayer = await client.fetch_user(curPlayerId)
            curPlayerDisplayName = curPlayer.display_name
            response, playerNames = await currentGame.playerCallUno(curPlayerId)
            embedResponse: discord.Embed
            if response == 0:
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed("You cannot call Uno if you are not in the current game"),
                    ephemeral = True
                )
                return
            elif response == 1:
                s = f"{curPlayerDisplayName}, you are now safe from Uno calls."
                embedResponse = getDefaultGameEmbed(s)
            elif response == 2:
                s = "There are no players with one card that have not called Uno."
                s2 = "Because the zprevious player had one card, you do not need to draw cards."
                embedResponse = getDefaultGameEmbed(s, s2)
            elif response == 3:
                s = "There are no players with one card that have not called Uno."
                s2 = "Because the previous player did not have one card, you will "
                s2 += f"be penalized. {UNO_PENALTY} cards have been drawn for you."
                embedResponse = getDefaultGameEmbed(s, s2)
            else:
                s = "There are players with one card that have not yet called Uno."
                s2 = f"The following players have been penalized and {UNO_PENALTY} "
                s2 += "cards have been drawn for each of them: "
                for playerName in playerNames:
                    p = await client.fetch_user(playerName)
                    s2 += f"{p.display_name}, "
                embedResponse = getDefaultGameEmbed(s, s2[:-2])
            await interaction.response.send_message(
                embed = embedResponse
            )
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is no active game.")
            )


@tree.command(name = "commands", description = "Lists all commands.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        commands: str = ""
        channelNames: str = ""
        descriptions: str = ""
        for command, (channelName, description) in unoCommands.items():
            commands += f"/{command}\n"
            channelNames += f"{channelName}\n"
            descriptions += f"{description}\n"
        embed = getDefaultMiscEmbed("Command List")
        embed.add_field(name = "Command", value = commands, inline = True)
        embed.add_field(name = "Channel", value = channelNames, inline = True)
        embed.add_field(name = "Description", value = descriptions, inline = True)
        await interaction.response.send_message(embed = embed)


@tree.command(name = "rules", description = "Rules of the game.", guild = discord.Object(id = UNO_SERVER_ID))
async def self(interaction: discord.Interaction):
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        await interaction.response.send_message(
            embed = getDefaultMiscEmbed("Rules", unoRules)
        )


client.run(TOKEN)
