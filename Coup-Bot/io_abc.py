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
    async def getPlayerInput(self, player):
        """Input for what a player wants to do on a turn.

        HANDLES INVALID INPUT BY DEFAULT.

        :raises UnoError: On invalid input"""
        pass

    @abstractmethod
    async def playerWon(self, player):
        """Output for when a player wins a game."""
        pass