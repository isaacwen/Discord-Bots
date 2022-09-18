from dotenv import load_dotenv
from discord.ui import Button, Select, View
from asyncio import Lock
from discord import SelectOption
from PIL import Image
import discord
import os
import logging

from io_abc import IO
from game import CoupGame, Player, PlayerMove, Character, MAX_PLAYERS, MIN_PLAYERS

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
playerQueueDisplayNames = []
playerQueueLock: Lock = Lock()
"""To prevent race conditions, this should be used whenever playerQueue or 
playerQueueDisplayNames is changed/used."""

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

cardPicImages = {
    "Ambassador": Image.open("card-images/Ambassador.png"),
    "Assassin": Image.open("card-images/Assassin.png"),
    "Captain": Image.open("card-images/Captain.png"),
    "Contessa": Image.open("card-images/Contessa.png"),
    "Duke": Image.open("card-images/Duke.png")
}

coupCommands = {
    "commands": [LOBBY_CHANNEL_NAME, "View all commands"],
    "rules": [LOBBY_CHANNEL_NAME, "View rules"],
    "queue": [LOBBY_CHANNEL_NAME, "View the current queue"],
    "joinqueue": [LOBBY_CHANNEL_NAME, "Join the queue"],
    "leavequeue": [LOBBY_CHANNEL_NAME, "Leave the queue"],
    "startgame": [LOBBY_CHANNEL_NAME, "Start a game"],
    "hand": [COUP_CHANNEL_NAME, "View current hand"],
    "gamestate": [COUP_CHANNEL_NAME, "View current game state"]
}
"""All commands currently available for public use. Each is associated with the
channel that it must be used in and a brief description."""

logging.basicConfig(
    level = logging.INFO,
    handlers = [logging.StreamHandler()]
)

with open("rules.txt", "r") as file:
    coupRules = file.read()


def getCardImageURL(cardCombination: str) -> str:
    """
    :param cardCombination: E.g. AssassinContessa
    :returns: URL to be used in embeds.
    """
    return f"https://i.imgur.com/{cardPicNames[cardCombination]}.png"


def generateHandCards(hand: list[str]) -> str:
    """ Uses PIL to generate PNG locally corresponding to the cards in hand.
    User is responsible for deleting temporary PNG afterwards.

    :param hand: List of characters in hand.
    :returns: Path to local PNG.
    """
    global cardPicImages
    baseDirectory = ""
    tempImageName: str = "tmp.png"

    imageSize = cardPicImages["Ambassador"].size
    handSize = len(hand)
    mergedImage = Image.new("RGB", (handSize * imageSize[0], imageSize[1]), (250, 250, 250))
    for i in range(handSize):
        mergedImage.paste(cardPicImages[hand[i]], (i * imageSize[0], 0))
    mergedImage.save(f"{tempImageName}", "PNG")
    return f"{baseDirectory}{tempImageName}"


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


class CoupBotIO(IO):
    """Defines I/O methods for Coup that is played in Discord."""

    validInputLock: Lock = Lock()
    """Acquired whenever the normal game flow is waiting for a user response,
    and released whenever a valid user response has been received."""
    rootLogger = logging.getLogger()

    async def acquireValidInputLock(self, logMessage: str):
        await self.validInputLock.acquire()
        self.rootLogger.info(f"validInputLock acquired: {logMessage}")

    def releaseValidInputLock(self, logMessage: str):
        self.validInputLock.release()
        self.rootLogger.info(f"validInputLock released: {logMessage}")

    async def displayMessage(self, message: str):
        await COUP_CHANNEL.send(embed = getDefaultGameEmbed(message))

    async def displayError(self, message: str):
        await COUP_CHANNEL.send(embed = getDefaultErrorEmbed(message))

    async def displayStatus(self, message: str):
        await COUP_CHANNEL.send(embed = getDefaultMiscEmbed(message))

    async def displayEmbed(self, embed: discord.Embed, view: View = None):
        if view:
            await COUP_CHANNEL.send(embed = embed, view = view)
        else:
            await COUP_CHANNEL.send(embed = embed)

    async def getInput(self, player = None) -> str:
        """Will be using Select and Button components to restrict user input, so
        this is not needed."""
        pass

    async def getPlayerInput(self, player: Player) -> PlayerMove:
        embedPlayerInput = getDefaultGameEmbed(
            f"{player.displayName}, it is your turn.",
            "Select the move that you want to make."
        )

        playerCoins = player.numCoins()
        validOptions: list[SelectOption] = []

        if playerCoins >= 10:
            validOptions = [
                SelectOption(label = "Coup", value = "Coup"),
                SelectOption(label = "Quit", value = "Quit")
            ]
        else:
            for pm in PlayerMove:
                if pm is PlayerMove.Coup and playerCoins < 7:
                    continue
                elif pm is PlayerMove.Assassinate and playerCoins < 3:
                    continue
                validOptions.append(SelectOption(
                    label = pm.name.replace("_", " "),
                    value = pm.name
                ))

        moveSelect = Select(
            placeholder = "Choose Move",
            options = validOptions
        )
        moveSelectView = View(timeout = None)
        moveSelectView.add_item(moveSelect)

        async def playerInputSelectResponse(interaction: discord.Interaction):
            correctUser: bool = interaction.user.id == player.name
            if correctUser:
                moveSelect.disabled = True
                moveSelect.placeholder = moveSelect.values[0].replace("_", " ")
            await interaction.response.edit_message(view = moveSelectView)
            return correctUser

        async def moveSelectCallback(interaction):
            if await playerInputSelectResponse(interaction):
                self.releaseValidInputLock(f"Player {player.name} has selected a valid move.")

        moveSelect.callback = moveSelectCallback

        await self.acquireValidInputLock(f"Waiting for Player {player.name} to select a valid move.")
        await self.displayEmbed(embed = embedPlayerInput, view = moveSelectView)

        await self.acquireValidInputLock(f"Confirmed that Player {player.name} has made a valid move.")
        self.releaseValidInputLock(f"Confirmed that Player {player.name} has made a valid move.")

        return PlayerMove[moveSelect.values[0]]

    async def getChallenges(self, curPlayer: Player, claimCharacter: Character, validPlayerNames: list[int]) -> int:
        challenger: int

        embedChallenges = getDefaultGameEmbed(
            f"Would anyone like to challenge {curPlayer.displayName}'s claim of {claimCharacter.name}?",
            "Note that `No` should only be pressed if no one would like to challenge."
        )

        noButton = Button(
            label = "No",
            style = discord.ButtonStyle.gray,
            custom_id = "noButton"
        )
        yesButton = Button(
            label = "Yes",
            style = discord.ButtonStyle.gray,
            custom_id = "yesButton"
        )

        challengesView = View(timeout = None)
        challengesView.add_item(noButton)
        challengesView.add_item(yesButton)

        async def challengesButtonResponse(button: Button, interaction: discord.Interaction) -> bool:
            """
            :returns: True if the user who clicked the button is not curPlayer.
                False otherwise"""
            notCurPlayer: bool = (interaction.user.id != curPlayer.name) and (interaction.user.id in validPlayerNames)
            if notCurPlayer:
                noButton.disabled, yesButton.disabled = True, True
                button.style = discord.ButtonStyle.blurple
            await interaction.response.edit_message(view = challengesView)
            return notCurPlayer

        async def noButtonCallback(interaction):
            if await challengesButtonResponse(noButton, interaction):
                nonlocal challenger
                challenger = -1
                self.releaseValidInputLock(f"No player is challenging Player {curPlayer.name}.")

        async def yesButtonCallback(interaction):
            if await challengesButtonResponse(yesButton, interaction):
                nonlocal challenger
                challenger = interaction.user.id
                self.releaseValidInputLock(f"Player {challenger} is challenging Player {curPlayer.name}.")

        noButton.callback = noButtonCallback
        yesButton.callback = yesButtonCallback

        await self.acquireValidInputLock(f"Waiting for any challengers.")
        await self.displayEmbed(embed = embedChallenges, view = challengesView)

        await self.acquireValidInputLock(f"Confirmed the following challenger: -1")
        self.releaseValidInputLock(f"Confirmed the following challenger: -1")

        return challenger

    async def getPlayerTargetChoice(self, player: Player, playerList: list[Player]) -> int:
        embedPlayerTarget = getDefaultGameEmbed(
            f"{player.displayName}, who would you like to target?",
            "Select the player that you would like to target."
        )

        playerOptions = []

        for i in range(0, len(playerList)):
            curPlayer = playerList[i]
            if curPlayer.name == player.name:
                continue
            playerOptions.append(SelectOption(
                label = curPlayer.displayName,
                value = str(i)
            ))

        playerTargetSelect = Select(
            placeholder = "Choose Player",
            options = playerOptions
        )
        playerTargetView = View(timeout = None)
        playerTargetView.add_item(playerTargetSelect)

        async def playerTargetSelectResponse(interaction: discord.Interaction):
            correctUser: bool = interaction.user.id == player.name
            if correctUser:
                playerTargetSelect.disabled = True
                playerTargetSelect.placeholder = playerList[int(playerTargetSelect.values[0])].displayName
            await interaction.response.edit_message(view = playerTargetView)
            return correctUser

        async def playerTargetCallback(interaction):
            if await playerTargetSelectResponse(interaction):
                self.releaseValidInputLock(f"Player {player.name} has chosen a target.")

        playerTargetSelect.callback = playerTargetCallback

        await self.acquireValidInputLock(f"Waiting for Player {player.name} to choose a target.")
        await self.displayEmbed(embed = embedPlayerTarget, view = playerTargetView)

        await self.acquireValidInputLock(f"Confirmed Player {player.name} has chosen a target.")
        self.releaseValidInputLock(f"Confirmed Player {player.name} has chosen a target.")

        return playerList[int(playerTargetSelect.values[0])].name

    async def getPlayerCardChoice(self, player: Player, isReveal: bool = True) -> int:
        playerCharacters: list[str] = [card.character.name for card in player.hand.cardList]
        revealedCardIndex: int

        revealDiscardString: str = "reveal" if isReveal else "discard"

        playerCardChosenFooter: str = None

        if len(playerCharacters) >= 2:
            playerCharactersUnique = sorted(set(playerCharacters.copy()))

            continueEmbed = getDefaultGameEmbed(
                f"{player.displayName} press Continue to choose a card to {revealDiscardString}."
            )
            continueButton = Button(label = "Continue", style = discord.ButtonStyle.gray)
            continueView = View(timeout = None)
            continueView.add_item(continueButton)

            playerCardChoiceEmbed = getDefaultGameEmbed(
                f"Which card would you like to {revealDiscardString}?"
            )
            playerCardChoiceOptions: list[SelectOption] = []
            for characterName in playerCharactersUnique:
                playerCardChoiceOptions.append(
                    SelectOption(label = characterName, value = characterName)
                )

            playerCardChoiceSelect = Select(
                placeholder = "Choose Card",
                options = playerCardChoiceOptions
            )
            playerCardChoiceView = View(timeout = None)
            playerCardChoiceView.add_item(playerCardChoiceSelect)

            async def continueButtonCallback(interaction: discord.Interaction):
                correctUser: bool = interaction.user.id == player.name
                if correctUser:
                    continueButton.disabled = True
                    continueButton.style = discord.ButtonStyle.blurple
                    await interaction.message.edit(view = continueView)
                    await interaction.response.send_message(
                        embed = playerCardChoiceEmbed,
                        view = playerCardChoiceView,
                        ephemeral = True
                    )
                else:
                    await interaction.response.edit_message(view = continueView)

            async def playerCardChoiceSelectCallback(interaction: discord.Interaction):
                playerCardChoiceSelect.disabled = True
                playerCardChoiceSelect.placeholder = playerCardChoiceSelect.values[0]
                self.releaseValidInputLock(f"Player {player.name} chose card to {revealDiscardString}")
                await interaction.response.edit_message(view = playerCardChoiceView)

            continueButton.callback = continueButtonCallback
            playerCardChoiceSelect.callback = playerCardChoiceSelectCallback

            await self.acquireValidInputLock(
                f"Waiting for Player {player.name} to choose card to {revealDiscardString}."
            )
            await self.displayEmbed(embed = continueEmbed, view = continueView)

            await self.acquireValidInputLock(f"Confirmed that Player {player.name} chose card to {revealDiscardString}")
            self.releaseValidInputLock(f"Confirmed that Player {player.name} chose card to {revealDiscardString}")

            for i in range(0, len(playerCharacters)):
                if playerCharacters[i] == playerCardChoiceSelect.values[0]:
                    revealedCardIndex = i
                    break
        else:
            playerCardChosenFooter = f"{player.displayName} has only one card, so it was chosen by default."
            revealedCardIndex = 0

        playerCardChosenEmbed = getDefaultGameEmbed(
            f"{player.displayName} has chosen to {revealDiscardString}:"
        )
        playerCardChosenEmbed.set_image(
            url = getCardImageURL(playerCharacters[revealedCardIndex])
        )
        playerCardChosenEmbed.set_footer(text = playerCardChosenFooter)

        await self.displayEmbed(playerCardChosenEmbed)
        return revealedCardIndex

    async def askPlayerContessa(self, player: Player) -> bool:
        claimContessa: bool

        askContessaEmbed = getDefaultGameEmbed(
            f"{player.displayName} would you like to claim Contessa?",
        )

        noButton = Button(
            label="No",
            style=discord.ButtonStyle.gray,
            custom_id="noButton"
        )
        yesButton = Button(
            label="Yes",
            style=discord.ButtonStyle.gray,
            custom_id="yesButton"
        )

        askContessaView = View(timeout = None)
        askContessaView.add_item(noButton)
        askContessaView.add_item(yesButton)

        async def askContessaButtonResponse(button: Button, interaction: discord.Interaction):
            correctUser: bool = interaction.user.id == player.name
            if correctUser:
                noButton.disabled, yesButton.disabled = True, True
                button.style = discord.ButtonStyle.blurple
            await interaction.response.edit_message(view = askContessaView)
            return correctUser

        async def noButtonCallback(interaction):
            if await askContessaButtonResponse(noButton, interaction):
                nonlocal claimContessa
                claimContessa = False
                self.releaseValidInputLock(f"Player {player.displayName} has chosen to not claim Contessa.")

        async def yesButtonCallback(interaction):
            if await askContessaButtonResponse(yesButton, interaction):
                nonlocal claimContessa
                claimContessa = True
                self.releaseValidInputLock(f"Player {player.displayName} has chosen to claim Contessa.")

        noButton.callback = noButtonCallback
        yesButton.callback = yesButtonCallback

        await self.acquireValidInputLock(
            f"Waiting for Player {player.displayName} to decide whether they want to claim Contessa."
        )
        await self.displayEmbed(embed = askContessaEmbed, view = askContessaView)

        await self.acquireValidInputLock(
            f"Confirmed {player.displayName} has chosen whether they want to claim Contessa."
        )
        self.releaseValidInputLock(
            f"Confirmed {player.displayName} has chosen whether they want to claim Contessa."
        )
        return claimContessa

    async def askPlayersRoles(self, characterList: list[Character], validPlayerNames: list[int]):
        retVal: tuple[int, Character]

        askRolesEmbed = getDefaultGameEmbed(
            f"Would any players like to claim any of the following roles?",
            "Note that `No Claims` should only be pressed if there is no one who wants to claim a character."
        )

        characterOptions = []
        for character in characterList:
            characterOptions.append(SelectOption(
                label = character.name,
                value = character.name
            ))

        askRolesSelect = Select(
            placeholder = "Claim Role",
            options = characterOptions
        )
        noClaimsButton = Button(
            label = "No Claims",
            style = discord.ButtonStyle.gray,
            custom_id = "noClaimsButton"
        )
        askRolesView = View(timeout = None)
        askRolesView.add_item(askRolesSelect)
        askRolesView.add_item(noClaimsButton)

        async def askRolesComponentResponse(interaction: discord.Interaction, button: Button = None):
            validPlayer: bool = interaction.user.id in validPlayerNames
            if validPlayer:
                askRolesSelect.disabled, noClaimsButton.disabled = True, True
                if button:
                    button.style = discord.ButtonStyle.blurple
                else:
                    askRolesSelect.placeholder = askRolesSelect.values[0]
            await interaction.response.edit_message(view = askRolesView)
            return validPlayer

        async def askRolesSelectCallback(interaction):
            if await askRolesComponentResponse(interaction):
                nonlocal retVal
                retVal = (interaction.user.id, Character[askRolesSelect.values[0]])
                self.releaseValidInputLock(f"Player {interaction.user.id} is claiming a role.")

        async def noClaimsButtonCallback(interaction):
            if await askRolesComponentResponse(interaction, noClaimsButton):
                nonlocal retVal
                retVal = (-1, None)
                self.releaseValidInputLock(f"No players claiming any roles.")

        askRolesSelect.callback = askRolesSelectCallback
        noClaimsButton.callback = noClaimsButtonCallback

        await self.acquireValidInputLock("Waiting if any players want to claim any roles.")
        await self.displayEmbed(embed = askRolesEmbed, view = askRolesView)

        await self.acquireValidInputLock("Confirmed if any players want to claim roles.")
        self.releaseValidInputLock("Confirmed if any players want to claim roles.")

        return retVal

    async def playerAssassinated(self, assassin: Player, assassinee: Player):
        await self.displayEmbed(getDefaultGameEmbed(
            f"{assassinee.displayName} has been assassinated by {assassin.displayName}."
        ))

    async def playerEliminated(self, player: Player):
        await self.displayEmbed(getDefaultGameEmbed(
            f"{player.displayName} has been eliminated."
        ))

    async def playerWon(self, player: Player):
        await self.displayEmbed(getDefaultGameEmbed(
            f"{player.displayName} has just won the game!"
        ))


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


@tree.command(name = "hand", description = "Shows current hand.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if await usedInAcceptedChannel(interaction, COUP_CHANNEL_ID, COUP_CHANNEL_NAME):
        playerName: int = interaction.user.id
        if currentGame:
            await currentGame.acquirePlayerLock(f"Viewing Player {playerName}'s hand.")
            handPNGPath: str = None
            try:
                player: Player = currentGame.getPlayerByName(playerName)
                playerCharacters: list[str] = [card.character.name for card in player.hand.cardList]
                playerCharacters.sort()
                handPNGPath = generateHandCards(playerCharacters)
                handPNGFile = discord.File(handPNGPath)
                handEmbed = getDefaultMiscEmbed(f"Coins: {str(player.numCoins())}")
                handEmbed.set_image(url = f"attachment://{handPNGPath}")
                await interaction.response.send_message(file = handPNGFile, embed = handEmbed, ephemeral = True)
            except Exception:
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed("There is not an active game/you aren't in the active game."),
                    ephemeral = True
                )
            finally:
                if handPNGPath and os.path.exists(handPNGPath):
                    os.remove(handPNGPath)
                currentGame.releasePlayerLock(f"Finished viewing player {playerName}'s hand")
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is not an active game/you aren't in the active game."),
                ephemeral = True
            )


@tree.command(name = "gamestate", description = "Shows the number of cards in each player's hand.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    if await usedInAcceptedChannel(interaction, COUP_CHANNEL_ID, COUP_CHANNEL_NAME):
        if currentGame:
            await currentGame.acquirePlayerLock("Viewing cards in each player's hands.")
            players: str = ""
            numCards: str = ""
            numCoins: str = ""
            for player in currentGame.players:
                players += player.displayName + "\n"
                numCards += str(player.handSize()) + "\n"
                numCoins += str(player.numCoins()) + "\n"
            currentGame.releasePlayerLock("Finished viewing cards in each player's hands.")

            embedGameState = discord.Embed(
                title = "Current Game State",
                color = EMBED_MISC_COLOR
            )
            embedGameState.add_field(name = "Player Name", value = players, inline = True)
            embedGameState.add_field(name = "# Cards", value = numCards, inline = True)
            embedGameState.add_field(name = "# Coins", value = numCoins, inline = True)
            embedGameState.add_field(name = "Turn Order", value = ":arrow_down:", inline = True)
            await interaction.response.send_message(embed = embedGameState)
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is not an active game.")
            )


@tree.command(name = "startgame", description = "Starts the Coup game.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    global playerQueue
    global playerQueueDisplayNames
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        if not currentGame:
            await playerQueueLock.acquire()
            if len(playerQueue) < MIN_PLAYERS:
                errorMessage = f"Unable to start game. {len(playerQueue)} out of a "
                errorMessage += f"minimum of {MIN_PLAYERS} players are in queue."
                await interaction.response.send_message(
                    embed = getDefaultErrorEmbed(errorMessage)
                )
                playerQueueLock.release()
                return
            frontQueue: list[int] = playerQueue[:MAX_PLAYERS]
            await interaction.response.send_message(
                embed = getDefaultMiscEmbed(
                    f"Starting Coup game with {len(frontQueue)} players.",
                    f"The maximum number of players in a game is {MAX_PLAYERS}."
                )
            )
            currentGame = CoupGame(
                playerQueue[:MAX_PLAYERS],
                playerQueueDisplayNames[:MAX_PLAYERS],
                CoupBotIO()
            )
            playerQueue = playerQueue[MAX_PLAYERS:]
            playerQueueDisplayNames = playerQueueDisplayNames[MAX_PLAYERS:]
            playerQueueLock.release()
            await currentGame.startGame()
            currentGame = None
        else:
            await interaction.response.send_message(
                embed = getDefaultErrorEmbed("There is already a game in progress.")
            )


@tree.command(name = "joinqueue", description = "Join queue for Coup.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global currentGame
    global playerQueue
    global playerQueueDisplayNames
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            player = interaction.user.id
            playerDisplayName = interaction.user.display_name

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
                playerQueueDisplayNames.append(playerDisplayName)
                embedQueue = discord.Embed(
                    title = "You have been added to the queue for the next game of Coup.",
                    description = "Use `/queue` to view your position in queue.\nUse `/leavequeue` to leave the queue.",
                    color = EMBED_MISC_COLOR
                )
                await interaction.response.send_message(
                    embed = embedQueue
                )


@tree.command(name = "leavequeue", description = "Leaves queue for Coup.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global playerQueue
    global playerQueueDisplayNames
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            player = interaction.user.id
            playerFound: bool = False
            for i in range(0, len(playerQueue)):
                if playerQueue[i] == player:
                    del playerQueue[i]
                    del playerQueueDisplayNames[i]
                    playerFound = True
                    break
            if playerFound:
                await interaction.response.send_message(
                    embed = getDefaultMiscEmbed("You have been removed from the queue for Coup.")
                )
            else:
                await interaction.response.send_message(
                    embed=getDefaultErrorEmbed("You were not in the queue.")
                )


@tree.command(name = "queue", description = "View current queue for Coup.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    global playerQueueDisplayNames
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        async with playerQueueLock:
            players: str = ""
            for playerDisplayName in playerQueueDisplayNames:
                players += playerDisplayName + "\n"

            if not players:
                players = "There are no players in queue currently."

            embedQueue = discord.Embed(
                title = "Queue for Coup (in order)",
                description = players,
                color = EMBED_MISC_COLOR
            )
            await interaction.response.send_message(
                embed = embedQueue
            )


@tree.command(name = "commands", description = "Lists all commands.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        commands: str = ""
        channelNames: str = ""
        descriptions: str = ""
        for command, (channelName, description) in coupCommands.items():
            commands += f"/{command}\n"
            channelNames += f"{channelName}\n"
            descriptions += f"{description}\n"
        embed = getDefaultMiscEmbed("Command List")
        embed.add_field(name = "Command", value = commands, inline = True)
        embed.add_field(name = "Channel", value = channelNames, inline = True)
        embed.add_field(name = "Description", value = descriptions, inline = True)
        await interaction.response.send_message(embed = embed)


@tree.command(name = "rules", description = "Rules of the game.", guild = discord.Object(id = COUP_SERVER_ID))
async def self(interaction: discord.Interaction):
    if await usedInAcceptedChannel(interaction, LOBBY_CHANNEL_ID, LOBBY_CHANNEL_NAME):
        await interaction.response.send_message(
            embed = getDefaultMiscEmbed("Rules", coupRules)
        )


client.run(TOKEN)
