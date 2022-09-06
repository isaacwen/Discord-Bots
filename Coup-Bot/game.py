from enum import Enum
from asyncio import Lock, get_event_loop
import random
import traceback
import logging

from io_abc import IO


class Character(Enum):
    Duke = 0
    Assassin = 1
    Captain = 2
    Ambassador = 3
    Contessa = 4


class PlayerMove(Enum):
    Income = 0
    Foreign_Aid = 1
    Coup = 2
    Tax = 3
    Assassinate = 4
    Steal = 5
    Exchange = 6
    Quit = 7


MAX_PLAYERS = 6
MIN_PLAYERS = 3
STARTING_COINS = 3
logging.basicConfig(
    level = logging.INFO,
    handlers = [logging.StreamHandler()]
)


class CoupError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Card:
    def __init__(self, character: Character):
        self.character: Character = character

    def __str__(self) -> str:
        return self.character.name

    def getCharacter(self) -> Character:
        return self.character


class CardList:
    """List of cards for deck, discard, and hands."""

    def __init__(self):
        self.cardList: list[Card] = []

    def __str__(self) -> str:
        s = ""
        for card in self.cardList:
            s += str(card) + "\n"
        return s

    def __len__(self) -> int:
        return len(self.cardList)

    def __add__(self, other):
        self.cardList += other.getCards()

    def add(self, card: Card):
        self.cardList.append(card)

    def addCards(self, otherCardList):
        self + otherCardList

    def pop(self) -> Card:
        """
        :returns: Top card from the CardList
        :raises CoupError: If there isn't a card in the CardList
        """
        try:
            return self.cardList.pop(0)
        except IndexError:
            raise CoupError("There are no cards remaining in the CardList.")

    def peek(self, n: int) -> Card:
        """Returns, but does not discard, nth card from the list.

        :param n: Index of card in list that should be revealed. Indexed
            starting from 0.
        :returns: nth card from list.
        :raises CoupError: n is an invalid index."""
        try:
            return self.cardList[n]
        except IndexError:
            raise CoupError("Invalid card selected.")

    def discard(self, n: int) -> Card:
        """Discards the nth card from the list.

        :param n: Index of card in list that should be discarded. Indexed
            starting from 0.
        :returns: discarded nth card from list.
        :raises CoupError: n is an invalid index."""
        try:
            return self.cardList.pop(n)
        except IndexError:
            raise CoupError("Invalid card selected.")

    def getCards(self) -> list[Card]:
        return self.cardList


class Deck(CardList):
    def __init__(self):
        super().__init__()
        for char in Character:
            for _ in range(0, 3):
                self.cardList.append(Card(char))
        self.shuffle()

    def popTwo(self) -> list[Card]:
        """
        :returns: Top two cards from the deck.
        :raises CoupError: If there are not two cards in the deck (there should
            always be 3 cards in the deck).
        """
        if len(self.cardList) < 2:
            raise CoupError("Deck has invalid number of cards.")
        retVal, self.cardList = self.cardList[:2], self.cardList[2:]
        return retVal

    def shuffle(self):
        random.shuffle(self.cardList)



class Player:
    def __init__(self, name: int, startingHand: list[Card]):
        self.name: int = name
        self.hand: CardList = CardList()
        self.coins: int = STARTING_COINS

        for card in startingHand:
            self.add(card)

    def __str__(self) -> str:
        s = "Player name: " + str(self.name) + "\nCards in hand:\n"
        for card in self.hand.getCards():
            s += str(card) + "\n"
        s += f"Coins: {self.coins}\n"
        return s

    def add(self, card: Card):
        self.hand.add(card)

    def addCoins(self, n: int):
        self.coins += n

    def removeCoins(self, n: int):
        """Removes n coins from player.

        :raises CoupError: If there are not enough coins."""
        if n > self.coins:
            raise CoupError(f"Player {self.name} does not have {n} coins ({self.coins} coins only). ")
        self.coins -= n

    def peek(self, n: int) -> Card:
        """Returns, but does not discrad, nth card from hand.

        :param n: Index of card in hand that should be revealed. Indexed
            starting from 0
        :returns: nth card from hand.
        :raises CoupError: n is an invalid index."""
        return self.hand.peek(n)

    def discard(self, n: int) -> Card:
        """Discards the nth card from hand.

        :param n: Index of card in hand that should be discarded. Indexed
            starting from 0
        :returns: discarded nth card from hand.
        :raises CoupError: n is an invalid index."""
        return self.hand.discard(n)

    def handSize(self) -> int:
        return len(self.hand)

    def numCoins(self) -> int:
        return self.coins

    def leave(self, discard: CardList):
        discard.addCards(self.hand)

    # TODO: remove method after testing
    def setHand(self, characters: list[Character]):
        """Sets the player's hand to have the given characters. Used for
        testing."""
        self.hand = CardList()
        for character in characters:
            self.hand.add(Card(character))


class TextBasedIO(IO):
    """Defines I/O methods for text based Coup that is played at the command
    line. This is implemented for testing purposes."""
    async def displayMessage(self, message: str):
        print(message)

    async def displayError(self, message: str):
        print(message)

    async def displayStatus(self, message: str):
        print(message)

    async def getInput(self, player: Player = None) -> str:
        if not player:
            return input("Input from anyone: ")
        else:
            return input(f"{str(player.name)} input: ")

    async def getPlayerInput(self, player: Player) -> PlayerMove:
        if player.numCoins() >= 10:
            return PlayerMove.Coup
        s = f"{str(player)}What move would you like to make?\n"
        for move in PlayerMove:
            s += f"{int(move.value) + 1}: {move.name}\n"
        await self.displayMessage(s)
        return PlayerMove(int(await self.getInput(player)) - 1)

    async def getChallenges(self, curPlayer: Player) -> int:
        return int(input("Enter name of player who would like to challenge (-1 otherwise): "))

    async def getPlayerTargetChoice(self, player: Player, playerList: list[int]) -> int:
        return int(input(f"{player.name}, enter name of player that you would like to target: "))

    async def getPlayerCardChoice(self, playerName: int, isReveal: bool = True) -> int:
        s = f"{playerName} which card would you like to "
        if isReveal:
            s += "reveal: "
        else:
            s += "discard: "
        return int(input(s))

    async def askPlayerContessa(self, playerName: int) -> bool:
        return bool(int(input(f"{playerName} would you like to claim contessa (0 or 1): ")))

    async def playerAssassinated(self, assassinName: int, assassineeName: int):
        print(f"{assassineeName} has been assassinated by {assassinName}.")

    async def playerEliminated(self, playerName: int):
        print(f"{playerName} has been eliminated.")

    async def playerWon(self, player: Player):
        await self.displayMessage(f"{str(player.name)} has just won the game!")


class CoupGame:
    """Provides all logic and manages all classes to run a game of Coup."""

    def __init__(self, playerNames: list[int], ioManager: IO):
        if not playerNames:
            raise CoupError("No players playing the game.")

        self.ioManager = ioManager

        self.deck: Deck = Deck()
        self.discard: CardList = CardList()

        self.playerNames: list[int] = []
        """Direct access to playerNames requires managing playerLock."""
        self.players: list[Player] = []
        """Direct access to players requires managing playerLock."""
        self.playerLock: Lock = Lock()
        """To prevent race conditions, this lock should be used whenever 
        playerNames or players is changed/used. Use the corresponding custom
        acquire/release methods."""

        random.shuffle(playerNames)
        for playerName in playerNames:
            self.addPlayer(playerName)

        self.rootLogger = logging.getLogger()

        self.rootLogger.info("Initialization of UnoGame finished successfully.")

    def __str__(self) -> str:
        s = f"Game state:\n\nDeck:\n{str(self.deck)}\n\nDiscard\n{str(self.discard)}\n\nPlayers:\n"
        for player in self.players:
            s += str(player) + "\n"
        return s

    async def acquirePlayerLock(self, logMessage: str):
        await self.playerLock.acquire()
        self.rootLogger.info(f"playerLock acquired: {logMessage}")

    def releasePlayerLock(self, logMessage: str):
        self.playerLock.release()
        self.rootLogger.info(f"playerLock released: {logMessage}")

    def addPlayer(self, playerName: int):
        """Adds a player into the game, if the max number of players has not
        yet been exceeded and if that player is not already in the game.

        Locks: does not check playerLock

        :raises CoupError: If max number of players has been exceeded or the
            given player is already in the game."""
        if len(self.players) >= MAX_PLAYERS:
            raise CoupError(f"The max number of players ({MAX_PLAYERS}) has been reached.")
        elif playerName in self.playerNames:
            raise CoupError("You are already in the game.")
        self.playerNames.append(playerName)
        self.players.append(Player(playerName, self.deck.popTwo()))

    async def executeTurn(self) -> bool:
        """Executes all logic for the next player's turn.

        :returns: Whether there is only one player remaining in the game at any
            point during this turn or not."""

        # TODO: remove this after testing
        print(self)

        curPlayer: Player = self.players[0]
        playerLeft: bool = False
        """Set to true if curPlayer quits or is eliminated on this turn."""

        pm = await self.ioManager.getPlayerInput(curPlayer)
        if pm is PlayerMove.Income:
            await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed move {pm.name}.")
            curPlayer.addCoins(1)
            self.releasePlayerLock("Player has finished taking income.")
        elif pm is PlayerMove.Foreign_Aid:
            await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed move {pm.name}.")
            curPlayer.addCoins(2)
            self.releasePlayerLock("Player has chosen to take foreign aid.")
        elif pm is PlayerMove.Quit:
            await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed move {pm.name}.")
            curPlayer.leave(self.discard)
            del self.players[0]
            playerLeft = True

            self.releasePlayerLock("Player has successfully quit the game.")
        elif pm is PlayerMove.Assassinate:
            targetPlayerName: int = await self.ioManager.getPlayerTargetChoice(curPlayer, self.playerNames)
            targetPlayer: Player = self.getPlayerByName(targetPlayerName)
            retVal = await self.resolveChallenges(curPlayer, Character.Assassin)
            if retVal == -2:
                return True
            elif retVal == curPlayer.name:
                if not curPlayer.handSize():
                    playerLeft = True
            elif retVal == targetPlayerName and not targetPlayer.handSize():
                pass
            # Only if the current player has not been successfully challenged
            else:
                loseCoins: bool = True
                """If curPlayer should lose 3 coins."""
                continueAssassinate: bool = True
                """If curPlayer successfully assassinates targetPlayer."""
                if await self.ioManager.askPlayerContessa(targetPlayerName):
                    retVal2 = await self.resolveChallenges(targetPlayer, Character.Contessa)
                    if retVal2 == -2:
                        return True
                    elif retVal2 == -1:
                        continueAssassinate = False
                    # If someone has challenged
                    else:
                        # If the target player falsely claims Contessa
                        if retVal2 == targetPlayerName:
                            # If the target player has died because of false
                            # claim of Contessa, don't continue assassination.
                            if not targetPlayer.handSize():
                                loseCoins = False
                                continueAssassinate = False
                        # If the target player has Contessa and someone
                        # unsuccessfully challenges.
                        else:
                            continueAssassinate = False

                        if retVal2 == curPlayer.name and curPlayer.handSize() == 0:
                            playerLeft = True

                if loseCoins:
                    await self.acquirePlayerLock(f"Removing coins from Player {curPlayer.name} for assassination.")
                    curPlayer.removeCoins(3)
                    self.releasePlayerLock(f"Finished removing coins from Player {curPlayer.name} for assassination.")

                if continueAssassinate:
                    discardedCardIdx = await self.ioManager.getPlayerCardChoice(targetPlayerName, False)
                    retVal3 = await self.playerDiscardCard(targetPlayerName, discardedCardIdx)
                    if retVal3 == 2:
                        return True
        else:
            await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed a move.")
            self.releasePlayerLock("Player has chosen another move.")
            print(f"You chose to {pm.name}.\n")

        if len(self.players) == 1:
            return True
        await self.updateNextPlayer(playerLeft)
        return False

    async def resolveChallenges(self, curPlayer: Player, claimCharacter: Character) -> int:
        """Ask if anyone would like to challenge and if so resolves the
        challenge.

        :param curPlayer: The player whose claim is being challenged.
        :param claimCharacter: The character which curPlayer is claiming.
        :returns: -1 if there are no challenges, -2 if there are challenges and
            the result is only one player remaining in the game, or the name of
            the player who LOST the challenge and has discarded a card if there
            are still players remaining after the challenge."""
        challengerName: int = await self.ioManager.getChallenges(curPlayer)
        if challengerName == -1:
            return challengerName
        revealedCardIdx: int = await self.ioManager.getPlayerCardChoice(curPlayer.name)
        revealedCard: Card = curPlayer.peek(revealedCardIdx)
        if revealedCard.getCharacter() is claimCharacter:
            # Challenged player shuffles claimed card back in the deck then gets
            # a random new one
            await self.acquirePlayerLock(f"{curPlayer.name} drawing new card.")
            self.deck.add(curPlayer.discard(revealedCardIdx))
            self.deck.shuffle()
            curPlayer.add(self.deck.pop())
            self.releasePlayerLock(f"{curPlayer.name} finished drawing new card.")

            discardedCardIdx: int = await self.ioManager.getPlayerCardChoice(challengerName, False)
            if (await self.playerDiscardCard(challengerName, discardedCardIdx)) == 2:
                return -2
            return challengerName
        else:
            discardedCardIdx: int = await self.ioManager.getPlayerCardChoice(curPlayer.name, False)
            if (await self.playerDiscardCard(curPlayer.name, discardedCardIdx)) == 2:
                return -2
            return curPlayer.name


    async def updateNextPlayer(self, playerLeft: bool):
        """Updates nextPlayer to the next player in the turn order.

        Locks: checks playerLock."""
        await self.acquirePlayerLock("Updating nextPlayer.")
        if not playerLeft:
            self.players.append(self.players.pop(0))
            self.playerNames.append(self.playerNames.pop(0))
        self.releasePlayerLock("Finished updating nextPlayer.")

    def getPlayerByName(self, name: int) -> Player:
        """Locks: does not check playerLock

        :returns: Player from current list of players with given name.
        :raises CoupError: If there are no players with the provided name."""
        for player in self.players:
            if player.name == name:
                return player
        raise CoupError("No player found with name: " + str(name))

    async def playerDiscardCard(self, playerName: int, n: int) -> int:
        """Discards the nth card for the Player with name = playerName. Then
        deletes this player from the game if appropriate and invokes method to
        display that this player has been eliminated.

        Locks: does check playerLock.

        :returns: 0 if the player has cards remaining, 1 if the player has been
            eliminated and there are still >1 players remaining in the game, and
            2 otherwise.
        :raises CoupError: If there are no players with the provided name."""
        await self.acquirePlayerLock(f"Discarding card for {playerName}.")
        playerIdx: int = 0
        player: Player = None
        for p in self.players:
            if p.name == playerName:
                player = p
                break
            playerIdx += 1
        if not player:
            self.releasePlayerLock("Finished discarding cards.")
            raise CoupError(f"No player found with name {str(playerName)} when discarding cards.")
        self.discard.add(player.discard(n))
        if not player.handSize():
            del self.players[playerIdx]
            del self.playerNames[playerIdx]
            self.releasePlayerLock("Finished discarding cards.")
            await self.ioManager.playerEliminated(playerName)
            if len(self.players) > 1:
                return 1
            else:
                return 2
        else:
            self.releasePlayerLock("Finished discarding cards.")
            return 0

    async def startGame(self):
        """Locks: does not check playerLock"""
        self.rootLogger.info(f"Starting game with {len(self.playerNames)} players.")
        while not await self.executeTurn():
            pass
        await self.ioManager.playerWon(self.players[0])

    # TODO: remove after testing
    def setHand(self, playerIdx, characters: list[Character]):
        """Sets the corresponding player's hand to have the following list of
        characters. Used for testing."""
        self.players[playerIdx].setHand(characters)


async def startGame():
    players = [1, 2, 3]
    game = CoupGame(players, TextBasedIO())
    game.setHand(0, [Character.Assassin, Character.Contessa])
    game.setHand(1, [Character.Assassin, Character.Contessa])
    game.setHand(2, [Character.Assassin, Character.Contessa])
    print(game)
    await game.startGame()


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(startGame())
