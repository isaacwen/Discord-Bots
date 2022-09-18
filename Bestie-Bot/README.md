# Bestie Bot
This is a bot with several miscellaneous features, all of which are listed below.

Detailed installation instructions are not available for this bot, as this bot has been customized for a specific server (henceforth referred to as 'the server') with specific users.


# Features
## Counting Channel Leaderboard
The server has a counting channel, which is a popular channel in many discord servers where users collaborate and take turns sending messages to count starting from 0. This bot provides a leaderboard that displays which users have counted the most times in the counting channel and how many times each user has counted.

The number of times users have counted in total is approximately 10000, where individual users in the server have counted anywhere from 0 to nearly 2500 times.

### Counting Competition
A second Counting Channel Leaderboard is also available that displays the users which have counted the most times in the counting channel within a given time period. This is meant as a friendly competition where users can compete against each other in their timing and typing endurance. The only rule for this competition is that users cannot type consecutive numbers, to deincentivize users from using scripts or botting to try and out-count other users. All numbers that are counted within the designated time frame are included in both the competition leaderboard and the normal leaderboard. This leaderboard can be reset if users wish to hold additional counting competitions.

## Counting Channel Dibbing
Certain numbers in the counting channel, such as milestones or "meme" numbers, are often valued more than others. Users will often dib a number to try and ensure that they are the ones that "count" that particular number in the counting channel. A dibbing feature was added where users can dib a number using the `dib` command and users can view all existing dibs using the `dibs` command. The feature is meant as a way for users to easily keep track of and visualize all existing dibs, enhancing the existing dibbing system that was in place.

## Shared Courses
Users are able to add the courses that plan to take/are taking in the upcoming school term to the bot's database using a `addcourse` command. The courses that a person has added can be viewed using `mycourses` and deleted using `delcourse`.

After a user has added their courses to the bot's database, they are then able to view what courses they share with other users in the server using the `sharedwithme` command, which lists all courses that other users in the server share with them, along with the names of these other users. This allows users to easily identify classmates and study partners within their classes.

If a user is considering taking a course and is wondering which other users in the server are taking a particular course, they can use the `whoistaking` command with the course in question, which lists all the users in the server who have indicated that they are taking that course in the upcoming school term.

## Animated Emotes
Animated emotes are not available to the standard Discord user. Instead, Discord users must pay a premium, known as Discord Nitro, in order to be able to use animated emotes.

To support those who do not have Discord Nitro, the names of several animated emotes (as well as static emotes that are also not available to the standard Discord user) have been added as commands, and when a user uses one of these commands, the bot responds with the corresponding emote.

## Turtle
In the server, there is a pets and animals channel designated for pictures and discussion about users' pets and other animals. If a user sends a message in this channel including the word 'turtle' or sends a turle emoji in this channel, the bot will respond with 1 of 5 random messages, ranging from pictures of turtles to a fun fact about turtles.
