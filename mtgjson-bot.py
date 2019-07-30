#!/usr/bin/python3
import discord
from discord.ext import commands
import random
import codecs
import MySQLdb
import MySQLdb.cursors
import re
import string
import math
from symbols import emoji
import Levenshtein
import json
import logging

DATABASE_HOST = 'localhost'
DATABASE_USER = 'user'
USER_PASSWD = 'passwd'
DATABASE_NAME = 'db'
BOT_SECRET_TOKEN = ''
CONFIG_PATH = 'debug.log'

DELIMITER = ('<<', '>>')

LEVENSHTEIN = 'DELIMITER $$ DROP FUNCTION IF EXISTS LEVENSHTEIN $$ CREATE FUNCTION LEVENSHTEIN(s1 VARCHAR(255) CHARACTER SET utf8, s2 VARCHAR(255) CHARACTER SET utf8) RETURNS INT DETERMINISTIC BEGIN DECLARE s1_len, s2_len, i, j, c, c_temp, cost INT; DECLARE s1_char CHAR CHARACTER SET utf8; -- max strlen=255 for this function DECLARE cv0, cv1 VARBINARY(256); SET s1_len = CHAR_LENGTH(s1), s2_len = CHAR_LENGTH(s2), cv1 = 0x00, j = 1, i = 1, c = 0; IF (s1 = s2) THEN RETURN (0); ELSEIF (s1_len = 0) THEN RETURN (s2_len); ELSEIF (s2_len = 0) THEN RETURN (s1_len); END IF; WHILE (j <= s2_len) DO SET cv1 = CONCAT(cv1, CHAR(j)), j = j + 1; END WHILE; WHILE (i <= s1_len) DO SET s1_char = SUBSTRING(s1, i, 1), c = i, cv0 = CHAR(i), j = 1; WHILE (j <= s2_len) DO SET c = c + 1, cost = IF(s1_char = SUBSTRING(s2, j, 1), 0, 1); SET c_temp = ORD(SUBSTRING(cv1, j, 1)) + cost; IF (c > c_temp) THEN SET c = c_temp; END IF; SET c_temp = ORD(SUBSTRING(cv1, j+1, 1)) + 1; IF (c > c_temp) THEN SET c = c_temp; END IF; SET cv0 = CONCAT(cv0, CHAR(c)), j = j + 1; END WHILE; SET cv1 = cv0, i = i + 1; END WHILE; RETURN (c); END $$ DELIMITER ; '

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
    if ((message.author == client.user) or (message.author.bot)):
        return

    #if message.author.id == 206966878365679616:
        #match = re.search(r"^\!voice\s+(\d+)\s+(.+\Z)", message.content)
        #if match:
        #    await client.send_message(client.get_channel(match.group(1)), match.group(2))
        #await client.send_message(client.get_channel(279861790194532353), 'Test')
    
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
    
    def levenshteinSearch(term):
        termRange = math.ceil(len(term) / 3) + 1
        termFloor = len(term) - termRange
        termCeil = len(term) + termRange
                
        cur.execute("SELECT name FROM cards WHERE multiverseId > 0 and CHAR_LENGTH(name) >= '{0}' and CHAR_LENGTH(name) <= '{1}' ORDER BY multiverseId DESC".format(termFloor, termCeil))
        cardsToCheck = cur.fetchall()
        bestMatch = 0.0
        matchedCard = None
                
        for card in cardsToCheck:            
            ratio = Levenshtein.ratio(term, card['name'])

            if (ratio > bestMatch):                    
                bestMatch = ratio
                matchedCard = card['name']
        
        if (bestMatch >= .65):
            return stdSearch(matchedCard)
        else:
            return stdSearch(term)
        
    # Look up the card in the MySQL database
    def getCard(card):
        # Iterate through searches to find the card
        for query in [stdSearch, startsWithSearch, anywhereSearch, soundexSearch, levenshteinSearch]:
            result = query(card)
            if result:
                printInfo = []
                lastrow = ''
        
                for row in result:
                    if ((lastrow != row['setCode']) and (result[0]['name'] == row['name'])):
                        printInfo.append(row['setCode'] + ' ' + row['rarity'].upper()[0])
                        lastrow = row['setCode']
        
                result[0]['printings'] = ', '.join(printInfo)
                return result[0]
            
        return result
    
    def getMultiverseId(card):
        cur.execute("SELECT `multiverseId` FROM cards WHERE multiverseId > 0 and name LIKE '{0}' ORDER BY multiverseId DESC LIMIT 1".format(db.escape_string(card).decode()))
        return cur.fetchone()['multiverseId']

    def getScryfallId(card):
        cur.execute("SELECT `scryfallId` FROM cards WHERE multiverseId > 0 and name LIKE '{0}' ORDER BY multiverseId DESC LIMIT 1".format(db.escape_string(card).decode()))
        return cur.fetchone()['scryfallId']
    
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
            response += fixReminderText(decode(emojimize(card['text'].replace('*', '★')))) + '\n'
        
        if card['flavorText']:
            response += '*' + decode(card['flavorText']) + '*\n'
        
        if card['power'] or card['toughness']:
            response += '**' + decode(card['power'].replace('*', '★')) + '/' + decode(card['toughness'].replace('*', '★')) + '**' + '\n'
        
        if card['loyalty']:
            response += '**' + card['loyalty'] + '**\n'
        
        if card['printings']:
            response += '*' + card['printings'] + '*\n'
        
        if (getMultiverseId(card['name']) >= 9999999):
            response = '||' + response + '||'
        
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
        
        # No more than 5 cards, sorry
        del commands[5:]
        
        for command in commands:
            # advancedCommand = re.search(r"([tos]):(\S+)", command)
            # if advancedCommand:
            #     getAdvancedCard()
            
            # Strip punctuation
            retrievedCard = getCard(db.escape_string(command).decode())
            #retrievedCard['name'] = retrievedCard['name'].replace("’", "'")
            
            if retrievedCard:
                if (retrievedCard['name'] not in query):
                    query.append(retrievedCard['name'])
                    await message.channel.send(formatCard(retrievedCard))
            else:
                await message.channel.send('**No cards found.**\nPlease revise your query.')
                
        if (len(query)):
            writedown(query)

    if (message.content.find('!price') >= 0):
        # Get the card price
        cur.execute("""SELECT * FROM queries WHERE channel = {0} ORDER BY id DESC LIMIT 1""".format(message.channel.id))
        result = cur.fetchone()

        if (result == None):
            return

        resultList = result['query'].split('|')
        
        response = []
        
        # Find the image by the set and card number
        for item in resultList:
            price = json.loads(getCard(item)['prices'])
            purchase = json.loads(getCard(item)['purchaseUrls'])
            
            if (price['paper']['2019-05-26']):
                response.append(getCard(item)['name'] + ' *' + getCard(item)['setCode'] + ' ' + getCard(item)['rarity'] + '* $' + price['paper']['2019-05-26'])
                if (purchase['tcgplayer']):
                    response[-1] += '\n TCGPlayer: <' + purchase['tcgplayer'] +'>'

        await message.channel.send('\n'.join(response))


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
            # Check if it’s a back side of a card
            side = ''
            if (getCard(item)['side'] == 'b'):
                side = '&face=back'
            
            # SPOILERS!
            if (getMultiverseId(item) >= 9999998):
                response.append('||https://api.scryfall.com/cards/' + getScryfallId(item) + '?format=image' + side + '||')
            else:
                response.append('https://api.scryfall.com/cards/' + getScryfallId(item) + '?format=image' + side)
        
        await message.channel.send('\n'.join(response))
        
client.run(BOT_SECRET_TOKEN)
