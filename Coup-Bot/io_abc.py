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
    async def getInput(self, player = None) -> str:
        """Gets input, either from anyone in the group, when player is not
        specified, or from a specific player"""
        pass

    @abstractmethod
    async def getPlayerInput(self, player):
        """Input for what a player wants to do on a turn.

        HANDLES INVALID INPUT BY DEFAULT. This includes inputs requiring coins
        and the player does not have enough coins."""
        pass

    @abstractmethod
    async def getChallenges(self, curPlayer, claimCharacter, validPlayerNames) -> int:
        """Asks players if anyone would like to challenge and, if so, returns
        the name of the player who challenged.

        :param curPlayer: The player whose move who is being challenged (they
            cannot initiate a challenge on themselves).
        :param validPlayerNames: Names of players are in the game.
        :returns: Name of the player who challenges, or -1 otherwise."""
        pass

    @abstractmethod
    async def getPlayerTargetChoice(self, player, playerList) -> int:
        """Input for which other player one wants to target with their move"""
        pass

    @abstractmethod
    async def getPlayerCardChoice(self, player, isReveal: bool = True) -> int:
        """Asks a player which of their cards they would like to reveal/discard.
        Should return 0 automatically if player only has one card.

        :param player: Player who is being asked.
        :param isReveal: True if action is reveal, False if action is discard.
        :returns: 0 or 1, corresponding to the index of the card in the hand
            that the player would like to discard."""
        pass

    @abstractmethod
    async def askPlayerContessa(self, player) -> bool:
        """Asks a player if they would like to claim Contessa when they are
        being assassinated.

        :returns: True if player claims Contessa, False otherwise."""
        pass

    @abstractmethod
    async def askPlayersRoles(self, characterList, validPlayerNames):
        """Asks if there are any players that would like to claim to be any of
        the characters in the character list. Used for
            - asking if there are any Dukes when someone takes foreign aid
            - asking if there are any Ambassadors/Captains when someone steals

        :param validPlayerNames: Names of players that are in the game.
        :returns: Name of the player that claims a role and the role that they
            claim, otherwise (-1, None)."""
        pass

    @abstractmethod
    async def playerAssassinated(self, assassin, assassinee):
        """Output for when a player has been assassinated."""
        pass

    @abstractmethod
    async def playerEliminated(self, player):
        """Output for when a player is eliminated."""
        pass

    @abstractmethod
    async def playerWon(self, player):
        """Output for when a player wins a game."""
        pass