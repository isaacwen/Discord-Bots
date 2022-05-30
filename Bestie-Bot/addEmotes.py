# Isaac Wen, University of Waterloo
# This file is used to add emotes to the DB manually. Insert the emote command
# and a link to the image/gif then run the command to add

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

mydb = mysql.connector.connect(
    host =                      os.getenv('DB_HOSTNAME'),
    user =                      os.getenv('DB_USER'),
    password =                  os.getenv('DB_PASSWORD'),
    database =                  os.getenv('DB_NAME')
)
mycursor = mydb.cursor()

EMOTES_TABLE_NAME =             os.getenv('EMOTES_TABLE_NAME')

emotes = [
    ("--sadge", "https://emoji.discord.st/emojis/82e544e2-6b07-4e0d-84ea-58ef2e4730bc.png"),
    ("--madge", "https://cdn3.emoji.gg/emojis/9564-madge.png"),
    ("--nopers", "https://cdn.betterttv.net/emote/5ec39a9db289582eef76f733/3x.gif"),
    ("--nodders", "https://cdn.betterttv.net/emote/5eadf40074046462f7687d0f/3x.gif"),
    ("--peepohappy", "https://cdn.betterttv.net/emote/5a16ee718c22a247ead62d4a/3x.png"),
    ("--peepohands", "https://cdn.betterttv.net/emote/5c20e3432b99ae62dd04331b/3x.gif"),
    ("--pepepoint", "https://cdn.betterttv.net/emote/5fedefa19d7d952e4059e68c/3x.gif"),
    ("--coffinplz", "https://cdn.betterttv.net/emote/5e9e978c74046462f7674f9f/3x.gif"),
    ("--peepoleave", "https://cdn.betterttv.net/emote/5d9be805d2458468c1f4dbb3/3x.gif"),
    ("--noted", "https://cdn.betterttv.net/emote/5f402fe68abf185d76c7617a/3x.gif"),
    ("--elmofire", "https://cdn.betterttv.net/emote/5d76c43abd340415e9f32fb1/3x.gif"),
    ("--prayge", "https://cdn.betterttv.net/emote/5f3ef6123212445d6fb49f1a/3x.png"),
    ("--copium", "https://cdn.betterttv.net/emote/5f64475bd7160803d895a112/3x.png"),
    ("--monkaw", "https://cdn.betterttv.net/emote/5981e885eaab4f3320e73b18/3x.png"),
    ("--peepohey", "https://cdn.betterttv.net/emote/5e162859b640b52102c684f7/3x.gif"),
    ("--turtle", "https://cdn.betterttv.net/emote/61323436af28e956864bb298/3x.gif"),
    ("--goose", "https://cdn.betterttv.net/emote/61a46b0bb50549e7e50161c1/3x.gif")
]

def addEmotes():
    sql = "REPLACE INTO " + EMOTES_TABLE_NAME + " (command, link) VALUES (%s, %s)"
    mycursor.executemany(sql, emotes)
    mydb.commit()

if __name__ == '__main__':
    addEmotes()