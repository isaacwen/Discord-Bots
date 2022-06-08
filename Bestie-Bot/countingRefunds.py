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

COUNT_TABLE_NAME =              os.getenv('COUNT_TABLE_NAME')

refunds = [
    (11, 686098202197491718),
    (11, 689575549706043532),
    (3, 264268744077869056),
    (6, 743660651695702087),
    (2, 908971055559888928),
    (4, 315904899202416641)
]

def giveCountingRefunds():
    sql = f"UPDATE {COUNT_TABLE_NAME} SET count = count + %s WHERE userid = %s"
    mycursor.executemany(sql, refunds)
    mydb.commit()

if __name__ == '__main__':
    giveCountingRefunds()