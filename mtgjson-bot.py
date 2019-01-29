#!/usr/bin/python
import discord
from discord.ext import commands
import random
import codecs
import MySQLdb
import MySQLdb.cursors
import re
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
                     cursorclass=MySQLdb.cursors.DictCursor)        

cur = db.cursor()


client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    # Ignore message if this bot sent the message
    if message.author == client.user:
        return
    
    # Decode newlines and other unusual characters
    def decode(text):
        return codecs.escape_decode(bytes(text, "utf-8"))[0].decode("utf-8")
    
    # Replace symbols with emoji
    def emojimize(text):
        for key, value in emoji.items():
            text = text.replace(key, value)
        
        return text
    
    # Italicize all reminder text
    def fixReminderText(text):
        return re.sub(r'(\([^)]+\))', r'*\1*', text)
    
    # Search starting with
    def startsWithSearch(term):
        cur.execute("SELECT * FROM cards WHERE name LIKE '" + term + "%' LIMIT 1")
        return cur.fetchone()
    
    # Search anywhere
    def anywhereSearch(term):
        cur.execute("SELECT * FROM cards WHERE name LIKE '%" + term + "%' LIMIT 1")
        return cur.fetchone()
    
    # Search according to Soundex
    def soundexSearch(term):
        cur.execute("SELECT * FROM cards WHERE name SOUNDS LIKE '" + term + "' LIMIT 1")
        return cur.fetchone()
    
    # Look up the card in the MySQL database
    def lookup(card):
        # Iterate through searches to find the card
        for query in [startsWithSearch, anywhereSearch, soundexSearch]:
            result = query(card)
            if result:
                break
        else:
            return '**No cards found.**\nPlease revise your query.'
        
        # Build the response with the card data
        response = '**' + result['name'] + '**'
        
        if result['manaCost']:
            response += '    ' + emojimize(result['manaCost'])
        
        response += '\n'
        response += result['type'] + '\n'
        
        if result['text']:
            response += fixReminderText(decode(emojimize(result['text']))) + '\n'
        
        if result['flavorText']:
            response += '*' + decode(result['flavorText']) + '*\n'
        
        if result['power'] or result['toughness']:
            response += '**' + result['power'] + '/' + result['toughness'] + '**' + '\n'
        
        if result['loyalty']:
            response += '**' + result['loyalty'] + '**\n'
        
        return response
        
    # Get commands from messages, splitting on the defined delimiter
    # Always drop the first element
    commands = [segment.split(DELIMITER[1])[0] for segment in message.content.split(DELIMITER[0])]
    commands.pop(0)
    
    if (commands):
        [await message.channel.send(lookup(command)) for command in commands]

client.run(BOT_SECRET_TOKEN)
