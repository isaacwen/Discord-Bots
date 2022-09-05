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

    def discard(self, n: int) -> Card:
        """Discards the nth card from the list.

        :param n: Index of card in list that should be discarded. Indexed
            starting from 0.
        :returns: discarded nth card from list.
        :raises CoupError: n is an invalid index"""
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
        self.coins: int = 2

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

    def discard(self, n: int) -> Card:
        """Discards the nth card from hand.

        :param n: Index of card in hand that should be discarded. Indexed
            starting from 0
        :returns: discarded nth card from hand.
        :raises CoupError: n is an invalid index"""
        return self.hand.discard(n)

    def handSize(self) -> int:
        return len(self.hand)

    def numCoins(self) -> int:
        return self.coins

    def leave(self, discard: CardList):
        discard.addCards(self.hand)


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

        self.nextPlayer: int = 0
        """Player to go next."""

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

        :returns: Whether the player has won on this turn or not."""

        # TODO: remove this after testing
        print(self)

        curPlayer: Player = self.players[self.nextPlayer]
        playerQuit: bool = False

        pm = await self.ioManager.getPlayerInput(curPlayer)
        await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed a move.")
        if pm is PlayerMove.Income:
            curPlayer.addCoins(1)
            self.releasePlayerLock("Player has finished taking income.")
        elif pm is PlayerMove.Foreign_Aid:
            self.releasePlayerLock("Player has chosen to take foreign aid.")
            curPlayer.addCoins(2)
        elif pm is PlayerMove.Quit:
            curPlayer.leave(self.discard)
            del self.players[self.nextPlayer]
            playerQuit = True

            self.releasePlayerLock("Player has successfully quit the game.")
        else:
            self.releasePlayerLock("Player has chosen another move.")
            print(f"You chose to {pm.name}.\n")

        if len(self.players) == 1:
            self.nextPlayer = 0
            return True
        await self.updateNextPlayer(playerQuit)
        return False

    async def updateNextPlayer(self, playerQuit: bool):
        """Updates nextPlayer to the next player in the turn order.

        Locks: checks playerLock."""
        await self.acquirePlayerLock("Updating nextPlayer.")
        if not playerQuit:
            self.nextPlayer += 1
        if self.nextPlayer >= len(self.players):
            self.nextPlayer = 0
        self.releasePlayerLock("Finished updating nextPlayer.")

    async def startGame(self):
        """Locks: does not check playerLock"""
        self.rootLogger.info(f"Starting game with {len(self.playerNames)} players.")
        while not await self.executeTurn():
            pass
        await self.ioManager.playerWon(self.players[self.nextPlayer])


async def startGame():
    players = [1, 2, 3]
    game = CoupGame(players, TextBasedIO())
    print(game)
    await game.startGame()


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(startGame())
