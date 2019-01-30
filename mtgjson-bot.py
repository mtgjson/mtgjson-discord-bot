#!/usr/bin/python
import discord
from discord.ext import commands
import random
import codecs
import MySQLdb
import MySQLdb.cursors
import re
import string
from symbols import emoji

DATABASE_HOST = 'localhost'
DATABASE_USER = 'user'
USER_PASSWD = 'passwd'
DATABASE_NAME = 'db'
BOT_SECRET_TOKEN = ''

DELIMITER = ('<<', '>>')

try:
   from config import *
except ImportError:
   pass

db = MySQLdb.connect(host=DATABASE_HOST,  # your host, usually localhost
                     user=DATABASE_USER,  # your username
                     passwd=USER_PASSWD,  # your password
                     db=DATABASE_NAME,    # name of the database
                     charset='utf8',
                     use_unicode=True,
                     cursorclass=MySQLdb.cursors.DictCursor)        

cur = db.cursor()


client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    for g in client.guilds:
        print(g.name)

@client.event
async def on_message(message):
    # Ignore message if this bot sent the message
    if message.author == client.user:
        return
    
    # Decode newlines and other unusual characters
    def decode(text):
        return codecs.escape_decode(bytes(text, "utf-8"))[0].decode("utf-8")
    
    def encode(text):
        return codecs.escape_encode(bytes(text, "utf-8"))[0]
    
    # Replace symbols with emoji
    def emojimize(text):
        for key, value in emoji.items():
            text = text.replace(key, value)
        
        return text
    
    # Italicize all reminder text
    def fixReminderText(text):
        return re.sub(r'(\([^)]+\))', r'*\1*', text)
    
    # Search starting with
    def stdSearch(term):
        cur.execute("SELECT * FROM cards WHERE multiverseId > 0 and name LIKE '{0}' ORDER BY multiverseId ASC LIMIT 1000".format(term))
        return cur.fetchall()
    
    def startsWithSearch(term):
        cur.execute("SELECT * FROM cards WHERE multiverseId > 0 and name LIKE '{0}%' ORDER BY multiverseId ASC LIMIT 100".format(term))
        return cur.fetchall()
    
    # Search anywhere
    def anywhereSearch(term):
        cur.execute("SELECT * FROM cards WHERE multiverseId > 0 and name LIKE '%{0}%' ORDER BY multiverseId ASC LIMIT 100".format(term))
        return cur.fetchall()
    
    # Search according to Soundex
    def soundexSearch(term):
        cur.execute("SELECT * FROM cards WHERE multiverseId > 0 and name SOUNDS LIKE '{0}' ORDER BY multiverseId ASC LIMIT 100".format(term))
        return cur.fetchall()
        
    # Look up the card in the MySQL database
    def getCard(card):
        # Iterate through searches to find the card
        for query in [stdSearch, startsWithSearch, anywhereSearch, soundexSearch]:
            result = query(card)
            if result:
                printInfo = []
                lastrow = ''
        
                for row in result:
                    if lastrow != row['setCode']:
                        printInfo.append(row['setCode'] + ' ' + row['rarity'].upper()[0])
                        lastrow = row['setCode']
        
                result[0]['printings'] = ', '.join(printInfo)
                return result[0]
            
        return result
    
    def getSetCodeAndNumber(card):
        cur.execute("SELECT `setCode`, `number` FROM cards WHERE multiverseId > 0 and name LIKE '{0}' ORDER BY multiverseId DESC LIMIT 1".format(db.escape_string(card).decode()))
        return cur.fetchone()
    
    def removePunctuation(text):
        return re.sub('['+string.punctuation+']', '', text)
        
    def formatCard(card):
        # Build the response with the card data
        response = '**' + card['name'] + '**'
        
        if card['manaCost']:
            response += '    ' + emojimize(card['manaCost'])
        
        response += '\n'
        response += card['type'] + '\n'
        
        if card['text']:
            response += fixReminderText(decode(emojimize(card['text']))) + '\n'
        
        if card['flavorText']:
            response += '*' + decode(card['flavorText']) + '*\n'
        
        if card['power'] or card['toughness']:
            response += '**' + card['power'] + '/' + card['toughness'] + '**' + '\n'
        
        if card['loyalty']:
            response += '**' + card['loyalty'] + '**\n'
        
        if card['printings']:
            response += '*' + card['printings'] + '*\n'
        
        return response
    
    def writedown(commands):
        # Record found cards into database
        cur.execute("""INSERT INTO queries (user, channel, query) VALUES ({0}, {1}, '{2}')""".format(message.author.id, message.channel.id, db.escape_string('|'.join(commands)).decode()))
        db.commit()
        
    # Get commands from messages, splitting on the defined delimiter
    # Always drop the first element
    commands = [segment.split(DELIMITER[1])[0] for segment in message.content.split(DELIMITER[0])]
    commands.pop(0)
    
    if (commands):
        query = []
        for command in commands:
            # advancedCommand = re.search(r"([tos]):(\S+)", command)
            # if advancedCommand:
            #     getAdvancedCard()
            
            # Strip punctuation
            retrievedCard = getCard(db.escape_string(command).decode())
            
            if retrievedCard:
                query.append(retrievedCard['name'])
                await message.channel.send(formatCard(retrievedCard))
            else:
                await message.channel.send('**No cards found.**\nPlease revise your query.')
                
        if (len(query)):
            writedown(query)

    if (message.content.find('!image') >= 0):
        # Display image for card for last query in this channel
        cur.execute("""SELECT * FROM queries WHERE channel = {0} ORDER BY id DESC LIMIT 1""".format(message.channel.id))
        result = cur.fetchone()
        
        if (result == None):
            return
        
        resultList = result['query'].split('|')
        
        response = []
        
        # Find the image by the set and card number
        for item in resultList:
            cardInfo = getSetCodeAndNumber(item)
            response.append('https://img.scryfall.com/cards/normal/en/' + cardInfo['setCode'].lower() + '/' + cardInfo['number'] + '.jpg')
        
        await message.channel.send('\n'.join(response))
        
client.run(BOT_SECRET_TOKEN)
