# Uno Bot
This is a bot that runs a classic game of Uno. This bot is designed to run in two separate Discord channels, with one channel acting as a lobby where players can queue up for a game and review the rules/commands of the game and the other channel acting as a game channel, where a game of Uno, once started, will be played.

# Contents
- [Installation](#installation)
- [Command List](#commandList)
- [Gameplay](#gameplay)
  -  [Receiving Input](#receivingInput)
  -  [Full Turn Examples](#fullTurnExamples)
- [Error Handling Examples](#errorHandlingExamples)


# Installation <a name = "installation"></a>

1. Install Python 3.10+.
2. Download/clone repository locally.
3. Run `pip install -r requirements.txt` from the Uno-Bot directory.
4. In the Discord server that you would like this bot to run in, create two channels for the lobby and the game channel.
5. Configure a new bot on Discord Developer Portal with all Gateway Intents enabled. Add the bot to the server with Administrator privileges. For help, see the [Discord documentation](https://discord.com/developers/docs/getting-started).
6. Add all of the card pictures in 
7. Fill in the .env file with the corresponding information. See comments in .env file.
8. Run bot.py. 

# Command List <a name = "commandList"></a>

This section lists all the commands that are available and their corresponding functionality.

## Commands for Rules and Commands
Users can see the rules and commands using the `/rules` and `/commands` commands respectively:

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190531679-a2316e4a-ede7-4f53-b6dd-72731c999827.png" width = 600></p>

## Player Queue Commands
Users can queue for a game using the `/joinqueue` command:

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190532044-b9c234a4-4c8c-4b56-b139-cf9cdbf471ed.png" width = 500></p>

After queueing, users can view the current queue of players using the `/queue` command and users can leave the queue using the `/leavequeue` command.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190532084-ab044ffa-f8eb-4695-a5ad-052c703cf54b.png" width = 350></p>

Once enough players are in the queue, any user can start the game using the `/startgame` command.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190532227-fa63667d-5e5f-4b50-a1b8-d729e5f2373e.png" width = 325></p>

## Game Commands
When users are in a game, they can view their current cards that they have in their hand using the `/hand` command. The bot responds with an ephemeral message, which means that only the player who invoked the `/hand` command is able to view the message. This means that a player can view the cards in their hand without any of the other players seeing what cards they have.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190532411-1a5dd09f-da04-47ce-9768-1383fd27091a.png" width = 500></p>

While players are not able to view the exact cards that other players have, in classic Coup any player is entitled to the knowledge of how many cards and coins each other player has. This is replicated using the `/gamestate` command, which can be invoked by any player and publicly displays how many cards and coins each player has, as well as the turn order.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/189577872-2214a2f0-9d0d-47b1-bfae-4929080679d7.png" width = 300></p>



# Gameplay <a name = "gameplay"></a>
I will show examples of how the bot receives input from players throughout the game and I will also show some gameplay examples to demonstrate what a turns in a game run by this bot may look like.


## Receiving Input <a name = "receivingInput"></a>
At various stages in the game, players need to give inputs to the bot as to what they want to do. How this bot receives inputs varies slightly depending on the action, however all input is given through Button and Select (dropdown menus) components to simplify parsing player input (by avoiding custom player inputs entirely).

All methods of receiving input are directed at specific player(s). In each of these cases, Buttons and Selects will only accept input from the designated players. If other players (or users that are not in the game) attempt to respond to a prompt that is not directed at them, they prompt will not respond to their input.

Furthermore, whenever a player responds to a prompt, their response is preserved within the prompt. As can be observed in the following examples, if a user presses a Button, the Button that they press will be highlighted in blue. If a user chooses an option from a Select, that option will be the one displayed as the default value. In both cases, after the user has provided input all Buttons/Selects are disabled. Thus, the progression of moves and decisions made throughout the game can be view simply by reviewing the messages in the game channel in chronological order.

### Beginning of Turn
For example, when a player's turn begins and they need to declare an action for a turn, they are presented with a dropdown menu that they can select an action from. Only actions which a player can afford, given their current coins, are displayed. For example, in the following User 1 only has 2 coins, thus they do not have the option to Assassinate or Coup another player.

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/189581571-79925aaa-d844-4b21-a1ee-b5ac4aee839c.png" width=33% style="vertical-align: middle">
  <img src="https://user-images.githubusercontent.com/76772867/189581638-d73163db-b957-4575-bc9f-698bbf73a6db.png" width=33% style="vertical-align: middle">
  <img src="https://user-images.githubusercontent.com/76772867/189581689-195b9208-7de6-41f6-a6f3-4c1ff8b098ab.png" width=33% style="vertical-align: middle">
</p>

Compare this to when a player has more than 3 coins, at which point they gain the option to Assassinate another player

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/189582100-5863574b-d2fe-40e0-921e-4308aa2093b0.png" width=33% style="vertical-align: middle">
  <img src="https://user-images.githubusercontent.com/76772867/189582177-fce96976-362a-4443-9151-38736818e82e.png" width=33% style="vertical-align: middle">
</p>

and simliarly when a player has more than 7 coins, they gain the option to Coup another player.

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/189582434-eda47b1e-4530-40c6-9a2c-546634f714f2.png" width=33% style="vertical-align: middle">
  <img src="https://user-images.githubusercontent.com/76772867/189582460-665798f7-bfc6-48e2-959b-8f4175a776d8.png" width=33% style="vertical-align: middle">
</p>

Finally, when a player has more than 10 coins, they must Coup, so the only options that a player can choose from when they have more than 10 coins is to Coup or to quit the game.

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/189582995-b63b19d2-087b-4b2e-b2a8-05ca9fbf6e0b.png" width=33% style="vertical-align: middle">
  <img src="https://user-images.githubusercontent.com/76772867/189583049-afc7f90b-d9ae-481e-b731-6cfb40e1660c.png" width=33% style="vertical-align: middle">
</p>

### Targeting Players
When a player (referred to in this section as the 'acting player') wishes to Assassinate, Steal from, or Coup another player, they must select a player to target. A prompt will be displayed that will allow the acting player to choose a target from a list of all the players in the game. Note that this is done before challenges are resolved, such that a player will declare their target for Assassinate or Steal before players must decide whether they want to challenge or not.

For example, if User 1 claims that they are a Captain and wishes to Steal, they will then be prompted to choose which player they want to steal from.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190292120-ede4bcd9-022c-45a8-91d3-5ecdc8cf19d5.png" width = 400></p>


### Revealing/Discarding Cards
When players are challenged or when they lose a life, they must select what card to reveal/discard. The difference between this input and another other input requested from players is that that the options that a player has in terms of the cards that they can choose to reveal/discard must be hidden from all other players. This is implemented by asking for input from the player through an ephemeral message. Since ephemeral messages can only be invoked in Discord as part of an interaction (i.e. by clicking a button), a prompt is used before each instance where a player might need to reveal/discard a card.

For example, if User 1 claims that they are a Duke and wishes to Tax, then another player challenges their claim, User 1 must then choose to reveal a card out of the cards that they currently have in their hand.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190288082-d11fb4c9-1f42-4a2e-b73f-5239f318e35f.png" width = ></p>


### Challenging Claims <a name = "challengingClaims"></a>
Another instance when players provide input is when they want to challenge a claim another player makes. Whenever a player makes a claim (henceforth referred to as the 'claiming player'), a prompt is sent that any player other than the claiming player can respond to. If there are no players that want to challenge the claim, then one of the players aside from the claiming player can press `No` and the move associated with the claim with commence. However, if a player wants to challenge the claim (henceforth referred to as the 'challenging player'), then they can press the `Yes` Button, after which the claiming player is forced to reveal a card and either the claiming player or the challenging player will have to discard a card, when appropriate.

For example, we have that User 1 claims that they are a Duke and wishes to Tax. A prompt appears indicating that User 1 is claiming Duke and asks if anyone would like to challenge. If no one would like to challenge, then User 1 gets 3 coins and play commences.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190283372-c4fe358c-513b-4ec9-aca2-cf8b341edebb.png" width = 400></p>

If instead a player wishes to challenge User 1's claim of Duke, User 1 has to reveal a card. If the revealed card is a Duke, then the challenging player must discard a card.

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/190285094-2590adcd-e717-423a-8c42-715437c1aef6.png" width=37% valign = "middle">
  <img src="https://user-images.githubusercontent.com/76772867/190285176-8ae7468b-959f-4392-a5a9-18519132fa53.png" width=33% valign = "middle">
</p>

In contrast, if the revealed card is not a Duke, then the claiming player, User 1 in this case, would have to discard a card.


### Countering Claims
For certain actions, instead of challenging the corresponding claims players can also choose to counter the action by claiming an appropriate counter-role. For Foreign Aid and Steal, this is implemented by prompting if any players, instead of the claiming player, would like to claim the appropriate counter roles after challenges are resolved (if appropriate) and before the action is executed. For Assassinate, instead of prompting all players for Contessa, only the targeted player is prompted for whether they would like to claim Contessa. Note that all counter-claims are also subject to being challenged in the exact same way as normal claims for actions are.

Since, in the case of Foreign Aid and Steal, any number of players can claim counter-roles, the prompt for if any players have any counter-roles will loop until either a player successfully counters the claiming player's actions or if no one would like to try and counter the claiming player's action.

For example, if User 1 claims they are a Captain, declares a target to Steal from, and all challenges, if any, are resolved, then a prompt is sent for all the other users asking if anyone would like to make a counter-claim.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190301785-5e281da8-99c9-4852-b075-91ba847f6036.png" width = ></p>

Say that User 3 then makes a counter-claim that they are an Ambassador to block the Steal, but then gets challenged by User 1. User 3 then does not reveal a Duke, which means that he must discard a card and all users aside from User 1 are prompted again if anyone would like to counter-claim User 1's claim of a Captain.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190318161-5c4e2647-4c43-4564-bfc8-e1187dcea1de.png" width = 450></p>

Another example is if User 1 declares they want to Assassinate User 2. After challenges are resolved, User 2 is then prompted for whether they want to claim Contessa or not.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190319287-5518fe85-9b5c-4365-bd4d-f9384517c6b7.png" width = 400></p>

The process afterwards if a counter-claim is declared is very similar to the previous, except no second prompt is provided in the case that User 2 gets successfully challenged (see [Failed Challenge/Failed Contessa Claim on Assassinate](#doubleKillAssassinate)).


## Full Turn Examples <a name = "fullTurnExamples"></a>
I will now show some examples of turns to demonstrate implemented mechanics that have not been explored in the previous section.

### Ambassador <a name = "ambassador"></a>
This shows the sequence of prompts and messages that are sent when User 1 wants to Exchange and his claim of Ambassador is unchallenged.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190323442-78626db7-e9a8-4076-8071-46e350b961a5.png" width = 400></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190323560-1ff7c266-5e3e-41f4-a2d3-e75ce2788d74.png" width = 400></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190323798-37eb6872-c252-4244-aa41-2548ad7def74.png" width = 400></p>


### Failed Challenge/Failed Contessa Claim on Assassinate <a name = "doubleKillAssassinate"></a>
This is a continuation of the Assassin/Contessa example given in the [Countering Claims](https://github.com/isaacwen/Discord-Bots/edit/main/Coup-Bot/README.md#countering-claims) section. This demonstrates what a turn would look like for a player who gets successfully challenged on their claim of Contessa when they are being Assassinated, causing them to lose 2 lives, hence be eliminated from the game instantly.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190322652-bccada63-e70a-40cd-b024-40ba21add7eb.png" width = 400></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190322088-2bacd317-0aee-4170-8313-36aa53ef57e6.png" width = 400></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190322148-ebb817a3-d673-4c73-9308-aee76094d457.png" width = 400></p>


### End Game
When there is only one player remaining in the game, a end game message declaring the winner is displayed.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190324314-fc779474-641b-498d-b4be-b22b2e973f58.png" width = 400></p>


# Error Handling Examples <a name = "errorHandlingExamples"></a>
Whenever a command is used incorrectly, an appropriate error message is displayed.

For example, if there are not enough players in queue and a user uses the `/startgame` command, the following error message is shown in lobby:

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/189576605-efd24eb9-ed05-43bf-ad42-8b081d4de6bd.png" width = 500></p>

If a command is not being used in the correct channel, an ephemeral message is sent as a response indicating the channel that the command should be used in. This is to prevent the commands from cluttering up other channels in the server.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190527705-69414779-5996-4ea3-bc88-088459a12b26.png" width = 450></p>

No error handling is needed for player inputs, as players can only choose from a predetermined set of inputs that are all determined to be valid.

