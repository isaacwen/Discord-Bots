from abc import ABC, abstractmethod


class IO(ABC):
    """Abstract class for I/O for Uno game."""
    @abstractmethod
    async def displayMessage(self, message: str):
        """Displays a game message to the entire group."""
        pass

    @abstractmethod
    async def displayError(self, message: str):
        """Displays an error message to the entire group. Mainly for discord
        output."""
        pass

    @abstractmethod
    async def displayStatus(self, message: str):
        """Displays a status message to the entire group. Mainly for discord
        output."""
        pass

    @abstractmethod
    async def getInput(self, player=None) -> str:
        """Gets input, either from anyone in the group, when player is not
        specified, or from a specific player"""
        pass

    @abstractmethod
    async def getPlayerInput(self, player, topDiscard, numDraw):
        """Input for what a player wants to do on a turn.

        DOES NOT HANDLE INVALID INPUT BY DEFAULT - JUST THROWS ERROR.

        :param numDraw: The amount of cards that would be drawn from the top
            action card.
        :raises UnoError: On invalid input"""
        pass

    @abstractmethod
    async def getPlayerColorChoice(self, player):
        """Input for what color a player wants when they play a black card."""
        pass

    @abstractmethod
    async def displayFirstValidDrawnCard(self, playerName, validCard, totalDrawn):
        """Displays the result of a player drawing cards when they have nothing
        to play and they are not drawing for an action card.

        :param player: The player that is drawing.
        :param validCard: The first playable card that is drawn from the deck.
            If validCard is None, then there are no cards remaining in the deck.
        :param totalDrawn: The total number of cards that the player has added
            to their hand (number of cards before the first playable card."""
        pass

    @abstractmethod
    async def playerWon(self, player):
        """Output for when a player wins a game."""
        pass