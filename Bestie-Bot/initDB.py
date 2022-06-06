# Isaac Wen, Univserity of Waterloo
# This file is used to initialize the DB. Requires the database to be created
# and specified in the .env file

import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

mydb = mysql.connector.connect(
    host =                      os.getenv('DB_HOSTNAME'),
    user =                      os.getenv('DB_USER'),
    password =                  os.getenv('DB_PASSWORD'),
    database =                  os.getenv('DB_NAME')
)
mycursor = mydb.cursor()

COUNT_TABLE_NAME =              os.getenv('COUNT_TABLE_NAME')
COUNTING_UPDATE_TABLE_NAME =    os.getenv('COUNTING_UPDATE_TABLE_NAME')
COUNTING_DIBS_TABLE_NAME =      os.getenv('COUNTING_DIBS_TABLE_NAME')
TURTLE_FACTS_TABLE_NAME =       os.getenv('TURTLE_FACTS_TABLE_NAME')
EMOTES_TABLE_NAME =             os.getenv('EMOTES_TABLE_NAME')
COMP_COUNT_TABLE_NAME =         os.getenv('COMP_COUNT_TABLE_NAME')
COMP_DATES_TABLE_NAME =         os.getenv('COMP_DATES_TABLE_NAME')

COMP_START_TIME =               datetime.fromisoformat(os.getenv('COMP_START_TIME'))
COMP_END_TIME =                 datetime.fromisoformat(os.getenv('COMP_END_TIME'))


def initCountTable():
    sql = f"CREATE TABLE {COUNT_TABLE_NAME} (userid BIGINT PRIMARY KEY, count int);"
    mycursor.execute(sql)
    mydb.commit()

def initCountingUpdateTable():
    sql = f"CREATE TABLE {COUNTING_UPDATE_TABLE_NAME} (timeName varchar(255), timeValue DATETIME);"
    mycursor.execute(sql)
    sql = f"INSERT INTO {COUNTING_UPDATE_TABLE_NAME} (timeName, timeValue) VALUES ('current', '2022-01-01 00:00:00');"
    mycursor.execute(sql)
    mydb.commit()

turtleFacts = [
    ("Turtles live all over the world. Turtles can be found in many different climates and are classified as either aquatic, semi-aquatic or semi-terrestrial. But no matter where they live, all turtles need water for either swimming or soaking. Some also need to “bask” on dry land. The amount of each need depends on the specific species.",),
    ("Turtles and tortoises aren’t the same thing. Well, that’s not exactly true. The truth is that the term “turtle” is an umbrella term for all 200 species of the testudine group, including both turtles and tortoises, among others. So the word “turtle” may mean more than you first expected!",),
    ("Turtles are some of the oldest animals around. If you’ve never had a turtle, you might not know just how long their life spans can be. In general, turtles evolved millions of years ago, and as such are among the oldest groups of reptiles. As pets, certain species of turtles can live to be 10-150+!",),
    ("The largest turtles weigh more than a thousand pounds. You aren’t going to find these in your neighborhood pet store tank, but the largest sea turtle species—the leatherback turtle—can weigh between 600 and 2,000 pounds and grow up to 8 feet in length.",),
    ("A turtle’s shell is not an exoskeleton. Some people mistake a turtle’s hard outer shell for an exoskeleton, but it’s actually a modified rib cage that’s part of the vertebral column.",),
    ("Turtles have a second shell. Besides their outer shell, turtles also have a lower shell, called a plastron. The plastron usually joins with the upper shell—called the carapace—along both sides of the body to create a complete skeletal box.",),
    ("Turtles aren’t silent. Although they’re not likely to be as loud as dogs or cats, turtles do make a range of noises, anything from chicken-like clucks to dog-like barking, depending on the species.",),
    ("In some species, weather determines if turtle eggs become male or female. In certain species of turtles, within a viable range, lower temperatures lead to male eggs hatching, while higher temperatures lead to female hatchlings.",),
    ("Turtles lose their first “baby tooth” within an hour. Baby turtles, called hatchlings, have an “egg tooth” on their beak to help them hatch out of their shell. This tooth disappears approximately an hour after hatching.",)
]

def initTurtleFactsTable():
    sql = f"CREATE TABLE {TURTLE_FACTS_TABLE_NAME} (id INT AUTO_INCREMENT PRIMARY KEY, fact varchar(1000));"
    mycursor.execute(sql)
    sql = f"INSERT INTO {TURTLE_FACTS_TABLE_NAME} (fact) VALUES (%s)"
    mycursor.executemany(sql, turtleFacts)
    mydb.commit()

emotes = [
    ("--pepecry", "https://emoji.gg/assets/emoji/4185-pepe-cry.gif"),
    ("--amongus", "https://emoji.discord.st/emojis/8c137b4f-d1af-4a61-a3d1-b2709aa50daf.gif"),
    ("--poggersrow", "https://emoji.discord.st/emojis/PoggersRow.gif"),
    ("--pepejam", "https://emoji.discord.st/emojis/264df6e7-06b9-4e52-b6ee-f8d8eaac9b08.gif"),
    ("--coolpikachu", "https://emoji.discord.st/emojis/a54bcf87-d880-4d34-8d9f-53ff614a24a6.gif"),
    ("--hello", "https://emoji.discord.st/emojis/12f7ae8e-54e9-4e0a-a247-f62ee670e8a5.gif"),
    ("--hehe", "https://emoji.discord.st/emojis/cd9dbff5-c3bc-46b3-9b8d-9421a8d67387.gif"),
    ("--blobdance", "https://emoji.discord.st/emojis/c3749065-db69-43be-8f02-87b072606c6e.gif"),
    ("--bonk", "https://emoji.discord.st/emojis/71f028f1-aafa-49fc-bde4-94bca315d410.png")
]

def initEmotesTable():
    sql = f"CREATE TABLE {EMOTES_TABLE_NAME} (command varchar(255) PRIMARY KEY, link varchar(500));"
    mycursor.execute(sql)
    sql = f"INSERT INTO {EMOTES_TABLE_NAME} (command, link) VALUES (%s, %s)"
    mycursor.executemany(sql, emotes)
    mydb.commit()

def initCompetitionTables():
    sql = f"CREATE TABLE {COMP_COUNT_TABLE_NAME} (userid BIGINT PRIMARY KEY, count INT);"
    mycursor.execute(sql)
    sql = f"CREATE TABLE {COMP_DATES_TABLE_NAME} (timeName varchar(20) PRIMARY KEY, timeValue DATETIME);"
    mycursor.execute(sql)
    mydb.commit()

# Initialize the start and end dates for the competition
compDates = [
    ("start", COMP_START_TIME),
    ("end", COMP_END_TIME)
]

def initCompetition():
    sql = f"REPLACE INTO {COMP_DATES_TABLE_NAME} (timeName, timeValue) VALUES (%s, %s);"
    mycursor.executemany(sql, compDates)
    mydb.commit()

# Resets the table used to count in the competition
def resetCompetitionCounts():
    sql = f"DELETE FROM {COMP_COUNT_TABLE_NAME}"
    mycursor.execute(sql)
    mydb.commit()

def initCountingDibsTable():
    sql = f"CREATE TABLE {COUNTING_DIBS_TABLE_NAME} (userid BIGINT PRIMARY KEY, number INT UNIQUE KEY);"
    mycursor.execute(sql)
    mydb.commit()

initFunctions = [
    initCountTable,
    initCountingUpdateTable,
    initCountingDibsTable,
    initTurtleFactsTable,
    initEmotesTable,
    initCompetitionTables,
    initCompetition
]

if __name__ == "__main__":
    for func in initFunctions:
        try:
            func()
        except mysql.connector.errors.ProgrammingError:
            pass
    # Comment out this line unless resetting for competition
    # resetCompetitionCounts()