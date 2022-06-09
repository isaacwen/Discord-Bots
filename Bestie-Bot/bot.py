# Isaac Wen, University of Waterloo
# This file contains the main code to run Bestie Bot...

import discord
import mysql.connector
import random
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID =                      int(os.getenv('ISAAC_ID'))
COUNTING_CHANNEL_ID =           int(os.getenv('COUNTING_CHANNEL_ID'))
PETS_CHANNEL_ID =               int(os.getenv('PETS_CHANNEL_ID'))
WELCOME_CHANNEL_ID =            int(os.getenv('WELCOME_CHANNEL_ID'))
TEST_SERVER_ID =                int(os.getenv('TEST_SERVER_ID'))
COURSE_CHANNEL_ID =             int(os.getenv('COURSE_CHANNEL_ID'))
TOKEN =                         os.getenv('TOKEN')
YOUTUBE_LINK =                  os.getenv('YOUTUBE_LINK')

COUNT_TABLE_NAME =              os.getenv('COUNT_TABLE_NAME')
COUNTING_UPDATE_TABLE_NAME =    os.getenv('COUNTING_UPDATE_TABLE_NAME')
COUNTING_DIBS_TABLE_NAME =      os.getenv('COUNTING_DIBS_TABLE_NAME')
TURTLE_FACTS_TABLE_NAME =       os.getenv('TURTLE_FACTS_TABLE_NAME')
EMOTES_TABLE_NAME =             os.getenv('EMOTES_TABLE_NAME')
COMP_COUNT_TABLE_NAME =         os.getenv('COMP_COUNT_TABLE_NAME')
COMP_DATES_TABLE_NAME =         os.getenv('COMP_DATES_TABLE_NAME')
COURSES_TABLE_NAME =            os.getenv('COURSES_TABLE_NAME')
# tzinfo object for the current timezone
CUR_TIME_ZONE =                 pytz.timezone(os.getenv('CUR_TIME_ZONE'))

LEADERBOARD_SIZE =              os.getenv('LEADERBOARD_SIZE')

MAX_COURSES =                   os.getenv('MAX_COURSES')
COURSE_TERM =                   os.getenv('COURSE_TERM')
MAX_COURSE_NAME_LENGTH =        int(os.getenv('MAX_COURSE_NAME_LENGTH'))

mydb = mysql.connector.connect(
    host =                      os.getenv('DB_HOSTNAME'),
    user =                      os.getenv('DB_USER'),
    password =                  os.getenv('DB_PASSWORD'),
    database =                  os.getenv('DB_NAME')
)
mycursor = mydb.cursor()

intents = discord.Intents.default()
intents.members = True
intents.presences = True
# May need to enable in the future (Aug 31, 2022)
# intents.message_content = True
client = discord.Client(intents = intents)

with open("publicFeatures.txt", "r") as file:
    features = file.read()

MAXINT = 2147483647

# Retrieves the time from a txt file, gets all messages from the counting
# channel since that time, then adds all relevant messages to the DB.
async def updateCountingDB():
    # Retrieve last update time recorded in DB
    mycursor.execute(f"SELECT timeValue FROM {COUNTING_UPDATE_TABLE_NAME} WHERE timeName = 'current'")
    lastTime = mycursor.fetchall()[0][0]
    
    # Update the time recorded in DB
    updateDBTime()

    # Get all the messages sent in the counting channel since lastTime
    async for msg in COUNTING_CHANNEL.history(after = lastTime, limit = None):
        await updateUserCount(msg)

# Updates the stored time in DB to right now (uses UTC+0 timezone)
def updateDBTime():
    cur = datetime.utcnow()
    sql = "UPDATE {} SET timeValue = '{}' WHERE timeName = 'current'".format(COUNTING_UPDATE_TABLE_NAME, cur.strftime("%Y-%m-%d %H-%M-%S")) # YYYY-MM-DD HH-MM-SS
    mycursor.execute(sql)
    mydb.commit()

# Increments user's count of messages by 1 if the message is a number. Returns
# false if the message was not a number. Also increments the user's count of
# messages on the competition leaderboard if their message is within the start
# and end times
async def updateUserCount(msg):
    global prev_count_user

    updateDBTime()
    message = msg.content
    if not message.isdigit():
        return False
    # Increment the user's count on the normal leaderboard
    userid = msg.author.id
    sql = f"INSERT INTO {COUNT_TABLE_NAME} (userid, count) VALUES ({userid}, 1) ON DUPLICATE KEY UPDATE count = count + 1"
    mycursor.execute(sql)
    # Increment the user's count on the competition leaderboard if applicable
    cur = datetime.now(tz = CUR_TIME_ZONE)
    if cur >= COMP_START_TIME and cur <= COMP_END_TIME and userid != prev_count_user:
        sql = f"INSERT INTO {COMP_COUNT_TABLE_NAME} (userid, count) VALUES ({userid}, 1) ON DUPLICATE KEY UPDATE count = count + 1"
        mycursor.execute(sql)
    mydb.commit()
    prev_count_user = userid
    return True

# Returns a string corresponding to the display of the counts of the top
# counters in the given leaderboard (not including the header text for the
# leaderboard)
async def displayLeaderboard(tableName):
    sql = f"SELECT userid, count FROM {tableName} ORDER BY count DESC LIMIT {LEADERBOARD_SIZE}"
    mycursor.execute(sql)
    retVal = mycursor.fetchall()
    retString = ""
    if retVal:
        counter = 1
        for userid, count in retVal:
            retString += "\n" + str(counter) + ".\t" + (await client.fetch_user(userid)).display_name + ": " + str(count) + " numbers counted"
            counter += 1
    else:
        retString = f"\n<{YOUTUBE_LINK}>"
    return retString

@client.event
async def on_ready():
    global COUNTING_CHANNEL
    global PETS_CHANNEL
    global WELCOME_CHANNEL
    global COURSE_CHANNEL
    COUNTING_CHANNEL = client.get_channel(COUNTING_CHANNEL_ID)
    PETS_CHANNEL = client.get_channel(PETS_CHANNEL_ID)
    WELCOME_CHANNEL = client.get_channel(WELCOME_CHANNEL_ID)
    COURSE_CHANNEL = client.get_channel(COURSE_CHANNEL_ID)
    print('We have logged in as {0.user}'.format(client))

    global COMP_START_TIME
    global COMP_START_TIME_STRING
    global COMP_END_TIME
    global COMP_END_TIME_STRING
    global COMP_DATE_STRING
    sql = f"SELECT timeValue FROM {COMP_DATES_TABLE_NAME} ORDER BY timeName DESC;"
    mycursor.execute(sql)
    retVal = mycursor.fetchall()
    # Set time zone to Waterloo local time
    COMP_START_TIME = CUR_TIME_ZONE.localize(retVal[0][0])
    COMP_END_TIME = CUR_TIME_ZONE.localize(retVal[1][0])
    COMP_START_TIME_STRING = COMP_START_TIME.strftime("%I:%M:%S %p")
    COMP_END_TIME_STRING = COMP_END_TIME.strftime("%I:%M:%S %p")
    COMP_DATE_STRING = COMP_START_TIME.strftime("%m-%d-%Y")

    # Counting competition stored userid so that users cannot accumulate points for
    # consecutive messages
    global prev_count_user
    prev_count_user = 0

    # Does this twice to make sure that all messages are caught
    await updateCountingDB()
    await updateCountingDB()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    msg = message.content.lower()

    # DMs to the bot
    if not message.guild:    
        try:
            if msg == "-features":
                await message.channel.send(features)
            elif msg == "-shutdown" and message.author.id == ADMIN_ID:
                await message.channel.send("Shutting down")
                await client.close()
        except discord.errors.Forbidden:
            pass
        return
    
    # counting channel
    if message.channel == COUNTING_CHANNEL:
        if not await updateUserCount(message):
            if message.content == "-leaderboard":
                await COUNTING_CHANNEL.send("__**BIGGEST CHADS**__" + await displayLeaderboard(COUNT_TABLE_NAME))
            elif message.content == "-myscore":
                userid = message.author.id
                sql = f"SELECT count FROM {COUNT_TABLE_NAME} WHERE userid = {userid}"
                mycursor.execute(sql)
                retVal = mycursor.fetchall()
                if retVal:
                    await COUNTING_CHANNEL.send("{username} has counted {count} times!".format(username = message.author.display_name, count = retVal[0][0]))
                else:
                    await COUNTING_CHANNEL.send(f"<{YOUTUBE_LINK}>")
            elif message.content == "-competition":
                cur = datetime.now(tz = CUR_TIME_ZONE)
                if cur < COMP_START_TIME:
                    await COUNTING_CHANNEL.send("__**COMPETITION HAS NOT STARTED**__\nCompetition is on " + COMP_DATE_STRING + " from " + COMP_START_TIME_STRING + " to " + COMP_END_TIME_STRING + " ET.")
                elif cur < COMP_END_TIME:
                    await COUNTING_CHANNEL.send("__**COMPETITION IS UNDERWAY!**__\nCompetition will end at " + COMP_END_TIME_STRING + " ET. Current leaderboard:" + await displayLeaderboard(COMP_COUNT_TABLE_NAME))
                else:
                    await COUNTING_CHANNEL.send("__**COMPETITION HAS ENDED!**__\nThank you for participating! The final leaderboard: " + await displayLeaderboard(COMP_COUNT_TABLE_NAME))
            elif message.content == "-dibs":
                sql = f"SELECT userid, number FROM {COUNTING_DIBS_TABLE_NAME} ORDER BY number ASC"
                mycursor.execute(sql)
                retVal = mycursor.fetchall()
                if retVal:
                    retString = "__**CURRENT DIBS**__"
                    for userid, number in retVal:
                        retString += "\n**" + str(number) + "** has been dibbed by " + (await client.fetch_user(userid)).display_name
                    await COUNTING_CHANNEL.send(retString)
                else:
                    await COUNTING_CHANNEL.send("No one has dibbed any numbers yet!")
            elif message.content.startswith("-dib"):
                try:
                    dibbedNum = (msg.split())[1]
                    if int(dibbedNum) not in range(0, MAXINT + 1):
                        raise ValueError
                    sql = f"INSERT INTO {COUNTING_DIBS_TABLE_NAME} (userid, number) VALUES ({message.author.id}, {dibbedNum})"
                    mycursor.execute(sql)
                    mydb.commit()
                    await COUNTING_CHANNEL.send(f"You have just dibbed {str(dibbedNum)}!")
                # If there is no dibbed number provided or it is incorrect format
                except (ValueError, IndexError):
                    await COUNTING_CHANNEL.send("Incorrect usage of `-dib`. To dib a number, use `-dib INTEGER` with an integer in the range `[0, 2147483647]`.")
                except (mysql.connector.errors.IntegrityError):
                    await COUNTING_CHANNEL.send("You have already dibbed a number, or the number you attempted to dib has already been dibbed.")
            elif message.content == "-undib":
                sql = f"DELETE FROM {COUNTING_DIBS_TABLE_NAME} WHERE userid = {message.author.id}"
                mycursor.execute(sql)
                mydb.commit()
                await COUNTING_CHANNEL.send("You have undibbed your number.")
    
    # pets channel
    if message.channel == PETS_CHANNEL and ("🐢" == msg or "turtle" in msg.replace(" ", "")):
        await message.add_reaction("🐢")
        rand = random.randint(0,4)
        if rand == 0:
            await PETS_CHANNEL.send(":turtle:")
        elif rand == 1:
            await PETS_CHANNEL.send("I like turtles")
        elif rand == 2:
            rand2 = random.randint(1, 9)
            sql = f"SELECT fact FROM {TURTLE_FACTS_TABLE_NAME} WHERE id = {rand2}"
            mycursor.execute(sql)
            await PETS_CHANNEL.send(mycursor.fetchall()[0][0])
        elif rand == 3:
            await PETS_CHANNEL.send("https://emoji.discord.st/emojis/0d70b7bf-63a6-4b73-a55d-d81008c78094.png")
        elif rand == 4:
            await PETS_CHANNEL.send("https://static.tvtropes.org/pmwiki/pub/images/tmnt1987.jpeg")
    
    # walmart discord nitro
    if msg.startswith('--'):
        sql = f"SELECT link FROM {EMOTES_TABLE_NAME} WHERE command = '{msg}'"
        mycursor.execute(sql)
        retVal = mycursor.fetchall()
        if retVal:
            await message.channel.send(retVal[0][0])
        else:
            await message.channel.send("https://imgur.com/jscoGrl")
    
    # courses feature
    if message.channel == COURSE_CHANNEL:
        if message.content.startswith("-addcourse"):
            try:
                messageArray = msg.split()
                if len(messageArray) != 2:
                    raise IndexError
                course = (msg.split())[1].upper()
                if len(course) > MAX_COURSE_NAME_LENGTH:
                    raise ValueError
                sql = f"INSERT INTO {COURSES_TABLE_NAME} VALUES ({message.author.id}, '{course}')"
                mycursor.execute(sql)
                mydb.commit()
                await COURSE_CHANNEL.send(f"You have indicated that you are taking {course} in {COURSE_TERM}.")
            except (IndexError):
                await COURSE_CHANNEL.send(f"Incorrect usage of `-addcourse`. To indicate that you are going to be taking a certain course in {COURSE_TERM}, use `-addcourse COURSENAME`. There should be **no spaces** in the course name, for example ECON 101 should be instead written as ECON101.")
            except (ValueError):
                await COURSE_CHANNEL.send(f"What you entered is probably not a valid course name. To see what constitutes a valid course name, see the following guide: <{YOUTUBE_LINK}>")
            except (mysql.connector.errors.DatabaseError):
                await COURSE_CHANNEL.send(f"You already indicated you will be taking {MAX_COURSES} courses. If you are taking more than {MAX_COURSES} courses, good luck and my condolences. If you ever need study music, I recommend this livestream which has 24/7 music (I think 24/7 might be appropriate given your courseload): <{YOUTUBE_LINK}>")
        elif message.content == "-mycourses":
            sql = f"SELECT courseName FROM {COURSES_TABLE_NAME} WHERE userid = {message.author.id}"
            mycursor.execute(sql)
            retVal = mycursor.fetchall()
            if retVal:
                await COURSE_CHANNEL.send(f"You have indicated that you are taking the following courses in {COURSE_TERM}: " + ", ".join([tup[0] for tup in retVal]))
            else:
                await COURSE_CHANNEL.send(f"You have not indicated that you are taking any courses in {COURSE_TERM} yet.")
        elif message.content.startswith("-delcourse"):
            try:
                messageArray = msg.split()
                if len(messageArray) != 2:
                    raise IndexError
                course = (msg.split())[1].upper()
                if len(course) > MAX_COURSE_NAME_LENGTH:
                    raise ValueError
                sql = f"DELETE FROM {COURSES_TABLE_NAME} WHERE userid = {message.author.id} AND courseName = '{course}';"
                mycursor.execute(sql)
                mydb.commit()
                await COURSE_CHANNEL.send(f"You have removed {course} from your list of courses.")
            except (IndexError):
                await COURSE_CHANNEL.send(f"Incorrect usage of `-delcourse`. To delete a course from the list of course that you have indicated you will be taking, use `-delcourse COURSENAME`. There should be **no spaces** in the course name, for example ECON 101 should be instead written as ECON101.")
            except (ValueError):
                await COURSE_CHANNEL.send(f"What you entered is probably not a valid course name. To see what constitutes a valid course name, see the following guide: <{YOUTUBE_LINK}>")
        elif message.content.startswith("-whoistaking"):
            try:
                messageArray = msg.split()
                if len(messageArray) != 2:
                    raise IndexError
                course = (msg.split())[1].upper()
                if len(course) > MAX_COURSE_NAME_LENGTH:
                    raise ValueError
                sql = f"SELECT DISTINCT userid FROM {COURSES_TABLE_NAME} WHERE courseName = '{course}'"
                mycursor.execute(sql)
                retVal = mycursor.fetchall()
                if retVal:
                    await COURSE_CHANNEL.send(f"The following people have indicated they are taking {course} in {COURSE_TERM}: " + ", ".join([(await client.fetch_user(int(tup[0]))).display_name for tup in retVal]))
                else:
                    await COURSE_CHANNEL.send(f"No one has indicated that they are taking {course} in {COURSE_TERM} yet.")
            except (IndexError):
                await COURSE_CHANNEL.send(f"Incorrect usage of `-whoistaking`. To see who has indicated they are taking a particular course, use `-whoistaking COURSENAME`. There should be **no spaces** in the course name, for example ECON 101 should be instead written as ECON101.")
            except (ValueError):
                await COURSE_CHANNEL.send(f"What you entered is probably not a valid course name. To see what constitutes a valid course name, see the following guide: <{YOUTUBE_LINK}>")
        elif message.content == "-allcourses" and message.author.id == ADMIN_ID:
            sql = f"SELECT userid, courseName FROM {COURSES_TABLE_NAME} GROUP BY userid, courseName;"
            mycursor.execute(sql)
            retVal = mycursor.fetchall()
            if retVal:
                courseDict = {}
                for userid, courseName in retVal:
                    if userid in courseDict:
                        courseDict[userid].append(courseName)
                    else:
                        courseDict[userid] = [courseName]
                retString = f"**People have indicated that they are taking the following courses in {COURSE_TERM}**"
                for user, courses in courseDict.items():
                    retString += f"\n{(await client.fetch_user(user)).display_name} is taking " + ", ".join(courses)
                await COURSE_CHANNEL.send(retString)
            else:
                await COURSE_CHANNEL.send(f"No one has indicated they are taking any courses in {COURSE_TERM} yet.")

        
@client.event
async def on_member_join(member):
    await WELCOME_CHANNEL.send(f"Welcome to the server, {member.display_name}!")
    await WELCOME_CHANNEL.send("https://emoji.discord.st/emojis/f22c3899-10e6-4931-bddb-48998ce1da28.gif")

client.run(TOKEN)