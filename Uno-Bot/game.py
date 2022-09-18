from enum import Enum
from asyncio import Lock
import random
import traceback
import logging

from io_abc import IO


class Color(Enum):
    black = -1
    red = 0
    blue = 1
    green = 2
    yellow = 3


class Value(Enum):
    wild = -1
    drawFour = -2
    zero = 0
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5
    six = 6
    seven = 7
    eight = 8
    nine = 9
    skip = 10
    drawTwo = 11
    reverse = 12


class PlayerMove(Enum):
    playCard = 0
    # For when a player wants to draw a card, or when the top card of the deck
    # is a drawTwo or drawFour and they have no cards to play.
    drawCard = 1
    quitGame = 2


MAX_PLAYERS = 8
MIN_PLAYERS = 2
STARTING_HAND_SIZE: int = 7
UNO_PENALTY: int = 2
"""Number of cards a player draws if 'Uno!' is called on them."""

ACTION_CARD_VALUES: list[Value] = [
    Value.wild,
    Value.drawFour,
    Value.skip,
    Value.drawTwo,
    Value.reverse
]
"""Values of action cards, cards that cannot be the first card in discard pile.
Note: this is not according to formal Uno rules."""

logging.basicConfig(
    level = logging.INFO,
    handlers = [logging.StreamHandler()]
)


class UnoError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Card:
    def __init__(self, color: Color, value: Value):
        self.color: Color = color
        self.value: Value = value
        self.isActionCard: bool = value in ACTION_CARD_VALUES
        self.discardColor: Color = color
        """Represents chosen color of black cards."""

    def __str__(self) -> str:
        return "(" + str(self.color) + ", " + str(self.value) + ")"

    def __eq__(self, other):
        return self.color == other.color and self.value == other.value

    def __ne__(self, other):
        return self.color != other.color or self.value != other.value

    def matches(self, playedCard, topDrawAndActive: bool) -> bool:
        """
        :param topDrawAndActive: Denotes that the top card is either a drawTwo
            or drawFour and the only cards that would match are cards of the same
            value.
        :returns: Given self is the card on the top of the discard, determines
            whether playedCard is a valid move."""
        if (self.value is playedCard.value or
                (not topDrawAndActive and
                 (playedCard.color is Color.black or
                  self.discardColor is playedCard.color))):
            return True
        return False

    def correctColorValue(self, color: str, value: str) -> bool:
        """
        :returns: Whether the given color and value match with the color and
            value of the card."""
        return self.color.name == color and self.value.name == value


class Discard:
    """Discard pile"""

    def __init__(self):
        self.topCard: Card = None
        self.bottomCards: list[Card] = []

    def __str__(self) -> str:
        s = "Top Card: " + str(self.topCard) + "\nBottom Cards:\n"
        for card in self.bottomCards:
            s += str(card) + "\n"
        return s

    def addTop(self, card: Card):
        """Put a card to the top of the discard pile"""
        if self.topCard:
            self.bottomCards.append(self.topCard)
        self.topCard = card

    def addCardBottom(self, card: Card):
        """Put a card to the bottom of the discard pile"""
        self.bottomCards.append(card)

    def addCardsBottom(self, cards: list[Card]):
        """Puts cards to the bottom of the discard pile"""
        self.bottomCards += cards

    def top(self) -> Card:
        """See the top card on the Discard pile"""
        return self.topCard

    def shuffleBack(self) -> list[Card]:
        """
        :returns: Unshuffled cards from discard, except for top card"""
        tmp: list[Card] = self.bottomCards
        self.bottomCards = []
        return tmp


class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        # Add colored cards
        for color in range(0, 4):
            for value in range(1, 13):
                self.cards.append(Card(Color(color), Value(value)))
                if not (Value(value) is Value.zero):
                    self.cards.append(Card(Color(color), Value(value)))

        # Add black cards
        for value in range(-2, 0):
            for _ in range(0, 4):
                self.cards.append(Card(Color.black, Value(value)))

        # Shuffle when initializing deck
        self.shuffle()

    def __str__(self) -> str:
        s = "Cards:\n"
        for card in self.cards:
            s += str(card) + "\n"
        return s

    def shuffle(self):
        random.shuffle(self.cards)

    def pop(self, discard: Discard) -> Card:
        """
        :returns: Top card from the deck.
        :raises UnoError: If there isn't a card in the deck and the discard pile
            only has one card."""
        if len(self.cards) == 0:
            self.cards = discard.shuffleBack()
            if len(self.cards) == 0:
                raise UnoError("No cards remaining in deck.")
            self.shuffle()
        return self.cards.pop(0)

    def popNonAction(self) -> Card:
        """THIS SHOULD ONLY BE CALLED AT THE BEGINNING OF THE GAME TO INITALIZE
        DISCARD PILE. ASSUMES >0 NON-ACTION CARDS IN DECK.

        :returns: The first card in the deck that isn't an action card."""
        count: int = 0
        while self.cards[count].isActionCard:
            count += 1
        return self.cards.pop(count)

    def popStartingHand(self) -> list[Card]:
        """This should be used ONLY TO INITIALIZE A PLAYER'S HAND.

        :returns: Cards for a player's starting hand.
        :raises UnoError: There are not enough cards (this method is used
            incorrectly)."""
        if STARTING_HAND_SIZE > len(self.cards):
            raise UnoError("Invalid usage of popStartingHand.")
        retVal, self.cards = self.cards[:STARTING_HAND_SIZE], self.cards[STARTING_HAND_SIZE:]
        return retVal

    def addBottom(self, card: Card):
        """Adds card to the bottom of the deck."""
        self.cards.append(card)


class Player:
    def __init__(self, name: int, startingHand: list[Card]):
        self.hand: list[Card] = startingHand
        self.name: int = name

        self.unoSafe: bool = True

    def __str__(self) -> str:
        s = "Player name: " + str(self.name) + "\nCards in hand:\n"
        for card in self.hand:
            s += str(card) + "\n"
        return s

    def add(self, card: Card):
        self.hand.append(card)

    def seeCard(self, n: int) -> Card:
        """Returns the nth card from hand but does not discard it.

        :param n: Index of card in hand that should be returned. Indexed
            starting from 0
        :returns: nth card from hand.
        :raises UnoError: n is an invalid index"""
        try:
            return self.hand[n]
        except IndexError:
            raise UnoError('Invalid card selected from hand.')

    def discard(self, n: int) -> Card:
        """Discards the nth card from hand.

        :param n: Index of card in hand that should be discarded. Indexed
            starting from 0
        :returns: discarded nth card from hand.
        :raises UnoError: n is an invalid index"""
        try:
            return self.hand.pop(n)
        except IndexError:
            raise UnoError('Invalid card selected from hand.')

    def handSize(self) -> int:
        return len(self.hand)

    def quit(self, discard: Discard):
        """Invoked when player quits the game, and all cards are returned to
        the bottom of the discard pile."""
        discard.addCardsBottom(self.hand)


class TextBasedIO(IO):
    """Defines I/O methods for text based Uno that is played at the command
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

    async def getPlayerInput(self, player: Player, topDiscard: Card, numDraw) -> (PlayerMove, int):
        s = f"\n{str(player.name)} it is your turn.\n{str(player)}\nTop Card: {str(topDiscard)}\n"
        s += f"What move would you like to make?\n1: Play a Card\n"
        s += "2: Draw Cards\n3: Quit Game"
        await self.displayMessage(s)
        try:
            pm: PlayerMove = PlayerMove(int(await self.getInput(player)) - 1)
            if pm is PlayerMove.playCard:
                await self.displayMessage("Which card would you like to play?")
                return pm, int(await self.getInput(player)) - 1
            else:
                return pm, 0
        except ValueError:
            raise UnoError("Invalid input given when selecting move.")

    async def getPlayerColorChoice(self, player: Player) -> Color:
        """Input for what color a player wants when they play a black card.

        HANDLES INVALID INPUT - DOES NOT THROW ERRORS."""
        s = "What color would you like to choose?\n1: Red\n2: Blue\n3: Green\n"
        s += "4: Yellow"
        c: Color = None
        while not c:
            try:
                await self.displayMessage(s)
                c = Color(int(await self.getInput(player)) - 1)
            except ValueError:
                await self.displayMessage("Invalid input given when selecting a color.")
        return c

    async def displayFirstValidDrawnCard(self, player, validCard, totalDrawn):
        pass

    async def playerWon(self, player: Player):
        """Output for when a player wins a game."""
        await self.displayMessage(f"{str(player.name)} has just won the game!")

class UnoGame:
    """Provides all logic and manages all classes to run a game of Uno."""

    def __init__(self, playerNames: list[int], ioManager: IO):
        # If there are no players, raise an error
        if not playerNames:
            raise UnoError("No players playing the game.")

        self.ioManager = ioManager

        self.deck: Deck = Deck()
        self.discard: Discard = Discard()

        self.playerNames: list[int] = []
        """Direct access to playerNames requires managing playerLock."""
        self.players: list[Player] = []
        """Direct access to players requires managing playerLock."""
        self.playerLock: Lock = Lock()
        """To prevent race conditions, this lock should be used whenever 
        playerNames or players is changed/used. Use the corresponding custom
        acquire/release methods."""

        # Randomize player order
        random.shuffle(playerNames)
        for playerName in playerNames:
            self.addPlayer(playerName)

        self.nextPlayer: int = 0
        """Player to go next."""
        self.turnOrder: int = 1
        """turnOrder = 1 or -1. Changed with reverse action card."""

        # Note that how the following two properties are defined has the
        # following implications:
        #   - if (not numDraw) and skipNextPlayer => discard.topCard.value is
        #     Value.skip
        #   - if numDraw and skipNextPlayer => discard.topCard.value is either
        #     Value.drawTwo or Value.drawFour
        #   - if not numDraw or not skipNextPlayer => discard.topCard does not
        #     involve skipping

        self.numDraw: int = 0
        """If the top card is a drawTwo or a drawFour, how many cards does the
        next person have to draw due to action card chaining."""
        self.skipNextPlayer: bool = False
        """If the top card is an action card involving skipping a turn that has
        yet to be executed, set to True."""

        # This is used to implement calling 'Uno!' during a game. Whenever
        # someone plays a card such that they have only one card remaining, this
        # safeguard is turned off until the next player in order has confirmed
        # the move that they are trying to make. When someone calls 'Uno!':
        #   - if they have one card remaining and are not already safe, then
        #     they are marked as safe, with no other effects. This is indicated
        #     using an unoSafe property for that player's corresponding Player
        #     object.
        #   - else:
        #       - if there are any other players with one card remaining, each
        #         of those players draws two cards and they are marked as safe.
        #       - if there are no other players with one card remaining and the
        #         safeguard is on, nothing happens.
        #       - if there are no other players with one card remaining and the
        #         safeguard is not on, the player who called `Uno!` draws two
        #         cards.
        #
        # Note that a player's safe property is turned off immediately after
        # they confirm that they are playing a card. This means that a player
        # must say 'Uno!' right after even if they still have to choose a color
        # to be 100% safe.
        self.unoSafeguard: bool = False
        self.unoSafeguardLock: Lock = Lock()
        """To prevent race conditions, this lock should be used whenever 
        unoSafeguard is changed/used. Use the corresponding custom acquire/release 
        methods."""

        self.rootLogger = logging.getLogger()

        self.initDiscard()

        self.rootLogger.info("Initialization of UnoGame finished successfully.")

    def __str__(self) -> str:
        """
        :returns: String corresponds to the game state (all cards in each location)."""
        s = f"Game state:\n\nDeck:\n{str(self.deck)}\n\nDiscard:\n{str(self.discard)}\n\nPlayers:\n"
        for player in self.players:
            s += str(player) + "\n"
        return s

    def initDiscard(self):
        """Initializes discard pile with a non-action card from the deck."""
        self.discard.addTop(self.deck.popNonAction())

    async def acquireUnoSafeguardLock(self, logMessage: str):
        await self.unoSafeguardLock.acquire()
        self.rootLogger.info(f"unoSafeguardLock acquired: {logMessage}")

    def releaseUnoSafeguardLock(self, logMessage: str):
        self.unoSafeguardLock.release()
        self.rootLogger.info(f"unoSafeguardLock released: {logMessage}")

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

        :raises UnoError: If max number of players has been exceeded or the
            given player is already in the game."""
        if len(self.players) >= MAX_PLAYERS:
            raise UnoError(f"The max number of players ({MAX_PLAYERS}) has been reached.")
        elif playerName in self.playerNames:
            raise UnoError(f"You are already in the game.")
        self.playerNames.append(playerName)
        self.players.append(Player(playerName, self.deck.popStartingHand()))

    def updateActions(self, playedCard: Card):
        """When a card is played, update properties of UnoGame corresponding to
        the actions that should be taken for that card."""
        if playedCard.value is Value.reverse:
            self.turnOrder *= -1
        elif playedCard.value is Value.drawFour:
            self.skipNextPlayer = True
            self.numDraw += 4
        elif playedCard.value is Value.drawTwo:
            self.skipNextPlayer = True
            self.numDraw += 2
        elif playedCard.value is Value.skip:
            self.skipNextPlayer = True

    async def executeTurn(self) -> bool:
        """Executes all logic for the next player's turn.

        :returns: Whether the player has won on this turn or not."""

        # If the top card is a skip and has not been executed, skip this
        # player's turn
        if (not self.numDraw) and self.skipNextPlayer:
            await self.updateNextPlayer()
            self.skipNextPlayer = False
            return False

        curPlayer: Player = self.players[self.nextPlayer]
        validMoveMade: bool = False
        topDrawAndActive: bool = self.skipNextPlayer and self.numDraw
        pm: PlayerMove
        n: int
        playerQuit: bool = False

        while not validMoveMade:
            try:
                pm, n = await self.ioManager.getPlayerInput(curPlayer, self.discard.topCard, self.numDraw)
                await self.acquirePlayerLock(f"Player {curPlayer.name} has confirmed a move.")
                await self.acquireUnoSafeguardLock(f"Player {curPlayer.name} has confirmed a move.")
                if pm is PlayerMove.playCard:
                    playedCard: Card = curPlayer.seeCard(n)
                    if not self.discard.topCard.matches(playedCard, topDrawAndActive):
                        raise UnoError("Card cannot be played here.")
                validMoveMade = True
            except UnoError as e:
                await self.ioManager.displayError(e.message)
                self.releasePlayerLock(f"Error executing player {curPlayer.name}'s move.")
                self.releaseUnoSafeguardLock(f"Error executing player {curPlayer.name}'s move.")
            except Exception as e:
                print(e)
                traceback.print_exc()
                await self.ioManager.displayError("Invalid input given.")
                self.releasePlayerLock(f"Error executing player {curPlayer.name}'s move.")
                self.releaseUnoSafeguardLock(f"Error executing player {curPlayer.name}'s move.")

        # Move is verified to be valid, so now execute it
        if pm is PlayerMove.playCard:
            playedCard: Card = curPlayer.discard(n)
            if curPlayer.handSize() == 1:
                curPlayer.unoSafe = False
                self.unoSafeguard = True
            else:
                curPlayer.unoSafe = True
                self.unoSafeguard = False
            self.releaseUnoSafeguardLock("Finished updating unoSafeguard after player has made a move.")
            self.releasePlayerLock("Player has finished playing a card (may need to choose color still).")
            if playedCard.color is Color.black:
                playedCard.discardColor = await self.ioManager.getPlayerColorChoice(curPlayer)
            self.discard.addTop(playedCard)

            self.updateActions(playedCard)

            # If the player has run out of cards, return that player has won.
            if curPlayer.handSize() == 0:
                return True
        elif pm is PlayerMove.drawCard:
            # If the current player draws card(s), they are guaranteed to be safe.
            curPlayer.unoSafe = True
            self.unoSafeguard = False
            self.releaseUnoSafeguardLock("Finished updating unoSafeguard after player has made a move.")

            if topDrawAndActive:
                try:
                    for _ in range(0, self.numDraw):
                        self.playerDraw(curPlayer)
                except UnoError as e:
                    await self.ioManager.displayError(e.message)
                self.releasePlayerLock("Player has finished drawing cards.")

                # Reset the draw
                self.numDraw = 0
                self.skipNextPlayer = False
            else:
                numDrawn: int = 0
                validCard: Card = None
                try:
                    validCard = self.deck.pop(self.discard)
                    while not self.discard.topCard.matches(validCard, topDrawAndActive):
                        numDrawn += 1
                        curPlayer.add(validCard)
                        validCard = self.deck.pop(self.discard)
                except UnoError as e:
                    # There are no cards remaining in the deck
                    validCard = None
                self.releasePlayerLock("Player has finished drawing cards.")
                await self.ioManager.displayFirstValidDrawnCard(curPlayer.name, validCard, numDrawn)
                if validCard:
                    if validCard.color is Color.black:
                        validCard.discardColor = await self.ioManager.getPlayerColorChoice(curPlayer)
                    self.discard.addTop(validCard)
                    self.updateActions(validCard)
        else:
            self.unoSafeguard = False
            self.releaseUnoSafeguardLock("Finished updating unoSafeguard after player has made a move.")
            playerQuit = True
            # Put player's cards into discard pile
            self.discard.addCardsBottom(curPlayer.hand)
            # Remove player from the game
            del self.players[self.nextPlayer]

            self.releasePlayerLock("Player has successfully quit the game.")

            # If there is only one player left, that player wins
            if len(self.players) == 1:
                self.nextPlayer = 0
                return True

        # Update to the next player
        await self.updateNextPlayer(playerQuit)
        return False

    async def updateNextPlayer(self, playerQuit: bool = False):
        """Updates nextPlayer to the next player in the turn order.

        Locks: checks playerLock"""
        await self.acquirePlayerLock("Updating nextPlayer.")
        # If the current player has quit and the turn order is positive, then
        # shouldn't update nextPlayer.
        if not (playerQuit and self.turnOrder == 1):
            self.nextPlayer += self.turnOrder
        numPlayers: int = len(self.players)
        if self.nextPlayer < 0:
            self.nextPlayer = numPlayers - 1
        elif self.nextPlayer >= numPlayers:
            self.nextPlayer = 0
        self.releasePlayerLock("Finished updating nextPlayer.")

    def getPlayerByName(self, name: int) -> Player:
        """Locks: does not check playerLock

        :returns: Player from current list of players with given name.
        :raises UnoError: If there are no players with the provided name."""
        for player in self.players:
            if player.name == name:
                return player
        raise UnoError("No player found with name: " + str(name))

    def getPlayerHand(self, name: int) -> list[Card]:
        """Locks: does not check playerLock

        :raises UnoError:"""
        return self.getPlayerByName(name).hand

    def playerDraw(self, player: Player):
        """Locks: does not check playerLock

        :raises UnoError: If there isn't a card in the deck and the discard pile
            only has one card."""
        player.add(self.deck.pop(self.discard))

    async def playerCallUno(self, playerName: int) -> (int, list[int]):
        """Manages all actions if the given player calls Uno. Returns values
        instead of directly sending to output because certain values need
        processing in discord (e.g. player display names, ephemerals).

        Locks: checks playerLock and unoSafeGuardLock

        :returns:
            (0, None) if player playerName could not be found in the game.
            (1, None) if player playerName is declaring Uno for themselves.
            (2, None) if player playerName has called Uno not for themselves,
                with safeguard up, and there are 0 players not safe.
            (3, None) if player playerName has called Uno not for themselves,
                without safeguard up, and there are 0 players not safe.
            (4, x), x != None if player playerName has called Uno not for
                themselves and x are the names of players that are not safe."""
        await self.acquirePlayerLock(f"Executing player {playerName} calling 'Uno!'.")
        await self.acquireUnoSafeguardLock(f"Executing player {playerName} calling 'Uno!'.")

        unsafePlayersWithOneCard = []
        unsafePlayerNamesWithOneCard = []
        callingPlayer: Player = None
        """Player who called."""
        selfUno: bool = False
        """If the player calling uno is calling for themselves."""

        for player in self.players:
            if player.name == playerName:
                callingPlayer = player
                if player.handSize() == 1:
                    selfUno = True
                    break
                continue
            if player.handSize() == 1 and not player.unoSafe:
                unsafePlayersWithOneCard.append(player)
                unsafePlayerNamesWithOneCard.append(player.name)

        retVal: (int, list[int])
        if not callingPlayer:
            retVal = (0, None)
        elif selfUno:
            callingPlayer.unoSafe = True
            retVal = (1, None)
        elif not unsafePlayersWithOneCard and self.unoSafeguard:
            retVal = (2, None)
        elif not unsafePlayersWithOneCard:
            try:
                self.playerDraw(callingPlayer)
                self.playerDraw(callingPlayer)
            except UnoError as e:
                self.ioManager.displayError(e.message)
            retVal = (3, None)
        else:
            # There are players with one card and the calling player does not.
            try:
                for player in unsafePlayersWithOneCard:
                    player.unoSafe = True
                    self.playerDraw(player)
                for player in unsafePlayersWithOneCard:
                    self.playerDraw(player)
            except UnoError as e:
                self.ioManager.displayError(e.message)
            retVal = (4, unsafePlayerNamesWithOneCard)

        self.releaseUnoSafeguardLock(f"Finished executing player {playerName} calling 'Uno!'")
        self.releasePlayerLock(f"Finished executing player {playerName} calling 'Uno!'")
        return retVal

    async def startGame(self):
        """Locks: does not check playerLock"""
        self.rootLogger.info(f"Starting game with {len(self.playerNames)} players.")
        while not await self.executeTurn():
            pass
        await self.ioManager.playerWon(self.players[self.nextPlayer])


async def startGame():
    players = [1, 2, 3]
    game = UnoGame(players, TextBasedIO())
    print(game)
    await game.startGame()


if __name__ == "__main__":
    startGame()
