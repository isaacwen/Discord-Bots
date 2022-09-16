# Uno Bot
This is a bot that runs a (almost) classic game of Uno (see [Implementation Details](#implementationDetails)). This bot is designed to run in two separate Discord channels, with one channel acting as a lobby where players can queue up for a game and review the rules/commands of the game and the other channel acting as a game channel, where a game of Uno, once started, will be played.

# Contents
- [Implementation Details](#implementationDetails)
- [Installation](#installation)
- [Command List](#commandList)
- [Gameplay](#gameplay)
  -  [Receiving Input](#receivingInput)
  -  [Other Examples](#otherExamples)
- [Error Handling Examples](#errorHandlingExamples)

# Implementation Details <a name = "implementationDetails"></a>
The coup that is run through this bot is almost classic Uno, but with a couple differences. One such difference is a common enhancement that is added by players, where, after a player plays a +2 or +4 card, subsequent players can avoid having to draw by playing a card of the same value (+2 or +4, respectively), and the first player who cannot player a card that is of that value has to draw the sum of all cards that previous players would have drawn. For example, if 3 consecutive players played +2 cards, then the fourth player, if they don't have a +2 card to play, would have to draw 6 cards.

The second difference is, when players are drawing cards when they have run out of cards to play and draw a playable card, they do not get to choose whether they want to play the card or not. This implementation method is chosen because it is how the process of drawing cards is formally defined in Uno rules and because the alternative implementation, where users are able to choose to keep a playable card in their hand and keep drawing, can result in unfavorable interactions due to the limitations of ephemeral messages in Discord (i.e. when players are prompted on whether they want to keep a card in their hand or not, other users gain information about the card that the player has drawn).

Another difference is that this game only plays until one person has run out of cards, who wins, whereas classic Uno can be played until there is only one person remaining with cards, who loses.

A final implementation detail is how calling 'Uno!' is implemented. To see a full description of when and how 'Uno!' should be called, see the rules.txt file or the screenshot in [Commands for Rules and Commands](https://github.com/isaacwen/Discord-Bots/edit/main/Uno-Bot/README.md#commands-for-rules-and-commands). This implementation of calling 'Uno!' is designed to be as similar to how calling 'Uno!' in classic Uno is as possible.

# Installation <a name = "installation"></a>

1. Install Python 3.10+.
2. Download/clone repository locally.
3. Run `pip install -r requirements.txt` from the Uno-Bot directory.
4. In the Discord server that you would like this bot to run in, create two channels for the lobby and the game channel.
5. Configure a new bot on Discord Developer Portal with all Gateway Intents enabled. Add the bot to the server with Administrator privileges. For help, see the [Discord documentation](https://discord.com/developers/docs/getting-started).
6. Add all of the card pictures in the card-images directory as emojis in the server.
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

While players are not able to view the exact cards that other players have, in classic Uno any player is entitled to the knowledge of how many cards each other player has. This is replicated using the `/gamestate` command, which can be invoked by any player and publicly displays how many cards and coins each player has, as well as the turn order.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190556509-3501a1ab-5cbb-4163-ad95-c8e429b65872.png" width = 300></p>



# Gameplay <a name = "gameplay"></a>
I will show examples of how the bot receives input from players throughout the game and I will also show some gameplay examples to demonstrate other cards and edge cases.xx

## Receiving Input <a name = "receivingInput"></a>
At various stages in the game, players need to give inputs to the bot as to what they want to do. How this bot receives inputs varies slightly depending on the action, where input can be given through Button and Select (dropdown menus) components or by sending an emoji in the game channel.

All methods of receiving input are directed at a specific player. In each of these cases, Buttons and Selects will only accept input from the designated player and the bot will only scan for responses in the game channel from the designated player. If other players (or users that are not in the game) attempt to respond to a prompt that is not directed at them, they prompt will not respond to their input.

Furthermore, whenever a player responds to prompts with Buttons or Selects, their response is preserved within the prompt. As can be observed in the following examples, if a user presses a Button, the Button that they press will be highlighted in blue. If a user chooses an option from a Select, that option will be the one displayed as the default value. In both cases, after the user has provided input all Buttons/Selects are disabled. Thus, the progression of moves and decisions made throughout the game can be view simply by reviewing the messages in the game channel in chronological order.

### Beginning of Turn
For example, when a player's turn begins and they need to declare an action for a turn, they are presented with several buttons for which they can choose an action for their turn, as well as an image corresponding to the current top card of the discard pile.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190561905-57f5e5d6-0772-473f-b06b-dccc738491b5.png" width = 400></p>

### Playing a Card
If a player chooses to play a card, a prompt is displayed indicating that the player should respond with the emoji of the card that they want to play. Then, the player can confirm that they want to play that particular card.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190562525-166154b6-7ec9-4711-91b0-701ac972a945.png" width = 500></p>

If a player plays a card that is not in their hand, if they play a card that is not playable given the current top card of the discard pile, or if they click `No` if they do not confirm they wish to play the card they chose, then they are brought back to the beginning prompt for their turn.

<p float = "left" align = "center">
  <img src="https://user-images.githubusercontent.com/76772867/190562822-b0b22867-5dfc-4b40-b528-e69cd0c69094.png" width=33% valign = "top">
  <img src="https://user-images.githubusercontent.com/76772867/190562958-fe6e0cbc-e1ba-4799-8f1f-b0fde8f3f066.png" width=33% valign = "top">
  <img src="https://user-images.githubusercontent.com/76772867/190563228-edf14d97-b3d6-4099-9843-d93fcaae7634.png" width=33% valign = "top">
</p>

### Drawing Cards
If a player chooses to play a card, then confirms that they want to draw, they will automatically draw cards until they draw a playable card. After the first playable card is found, a message indicating how many cards the player has drawn in total as well as the first playable card itself is displayed.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190561721-a7717edc-ed64-4e5d-809c-8f27959855ab.png" width = 500></p>

#### Drawing on +2 and +4 cards
The exception to drawing cards is when the top card is a +2 and +4 card and it is still active, that is, prior players all played a card of this value. In this case, players are shown a message in the beginning prompt of their turn indicating that the top +2/+4 card is still active and how many cards the next player who chooses to draw must draw.

For example, we have that User 3 plays a +2 card on a non-active +2 (note that there is no message indicating that the inital +2 is active). On User 1's turn, we now see a message that the top +2 card is active. As User 1 also plays a +2 card, the message is updated in the beginning prompt for User 2's turn to show that User 2, if they choose to draw, must draw 4 cards.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190561082-6cd9e665-f3fd-467d-80ae-1457301b401e.png" width = 500></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190561246-3a60fc5d-1b15-42af-a955-8e8c0f86c060.png" width = 500></p>

### Choosing Colors on Black Cards
The last instance when players are prompted for input is when they play a black card, where the prompt has 4 buttons for each of the non-black colors. The user is able to select the color that they want the black card to have while at the top of the discard pile, and a corresponding message is displayed in the beginning prompt of the subsequent turn.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190564000-9b6e47d6-6fec-4074-808c-e2507677915b.png" width = 500></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190564089-74a3bfd2-e69a-45be-b7d9-b3a1bef19edf.png" width = 500></p>

This process is slightly different for +4 cards. Because the subsequent player can only play a +4 card or draw, what color the +4 card was chosen to be is not relevant. Thus, only the beginning prompt for the player afterwards will have the color that the +4 card was chosen to have, if another +4 card was not played on top.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190564737-365b6c7f-194d-44ae-bc60-f7040d597f73.png" width = 500></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190564802-ff8d3d96-c60a-4296-a538-93bfaad55c89.png" width = 500></p>


## Other Examples <a name = "otherExamples"></a>
I will now show some other examples of turns to demonstrate other cards and edge cases.

### Reverse Card
When a player plays the reverse card, the turn order is reversed, as can be seen when using the `/gamestate` command.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190569035-f0d739d5-a480-4106-b8d2-30d1f4f574cc.png" width = 500></p>
<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190569281-45591117-c805-433e-b505-452826574b67.png" width = 500></p>

### Skip Card
When a player plays the skip card, the next person in the turn order is skipped automatically.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190569887-803f5a6e-51ee-44fa-b7c5-a8ca465f90f9.png" width = 500></p>

### Drawing Black Card
When a player is drawing cards from the deck, aside from drawing as a result of +2 and +4 cards, a prompt to allow the player drawing cards to choose the color will be shown, as expected.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190572784-87655a5e-5ee0-471a-8fbd-293b56878705.png" width = 500></p>

### End Game
When one player has run out of cards, an end game message declaring the winner is displayed.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190573978-a3721de5-cb8d-4f3e-8cd9-dc4fd7080204.png" width = 400></p>


# Error Handling Examples <a name = "errorHandlingExamples"></a>
Whenever a command is used incorrectly, an appropriate error message is displayed.

For example, if there are not enough players in queue and a user uses the `/startgame` command, the following error message is shown in lobby:

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190574540-6f5a2407-b37d-40d0-8d88-7712f511ace2.png" width = 500></p>

If a command is not being used in the correct channel, an ephemeral message is sent as a response indicating the channel that the command should be used in. This is to prevent the commands from cluttering up other channels in the server.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190574669-2db78bdf-bd79-42e8-967d-3ad5f7d7c64a.png" width = 500></p>

There is only one instance where inputs can be accepted that are not from a predetermined set of inputs, which is when players choose to play a card during a turn and choose the card that they want to play using an emoji. If the input is not a valid card, then the input is rejected and a corresponding error message is displayed.

<p align = "center"><img src = "https://user-images.githubusercontent.com/76772867/190575457-edf8c506-20ce-45e8-b404-07f53c2553ce.png" width = 500></p>


