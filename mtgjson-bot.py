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
    
    def emojimize(text):
        for key, value in emoji.items():
            text = text.replace(key, value)
            
        return text
    
    def fixReminderText(text):
        return re.sub(r'(\([^)]+\))', r'*\1*', text)
    
    # Look up the card in the MySQL database
    def lookup(card):
        # For now, limiting 1, but in the future, we should distinguish cards
        cur.execute("SELECT * FROM cards WHERE name like '" + card + "' LIMIT 1")
        result = cur.fetchone()
        
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

#bot = commands.Bot(command_prefix='?', description='description')
#
#
#@bot.event
#async def on_ready():
#    print('Logged in as')
#    print(bot.user.name)
#    print(bot.user.id)
#    print('------')
#
#@bot.command()
#async def add(ctx, left: int, right: int):
#    """Adds two numbers together."""
#    await ctx.send(left + right)
#
#@bot.command()
#async def roll(ctx, dice: str):
#    """Rolls a dice in NdN format."""
#    try:
#        rolls, limit = map(int, dice.split('d'))
#    except Exception:
#        await ctx.send('Format has to be in NdN!')
#        return
#
#    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
#    await ctx.send(result)
#
#@bot.command(description='For when you wanna settle the score some other way')
#async def choose(ctx, *choices: str):
#    """Chooses between multiple choices."""
#    await ctx.send(random.choice(choices))
#
#@bot.command()
#async def repeat(ctx, times: int, content='repeating...'):
#    """Repeats a message multiple times."""
#    for i in range(times):
#        await ctx.send(content)
#
#@bot.command()
#async def joined(ctx, member: discord.Member):
#    """Says when a member joined."""
#    await ctx.send('{0.name} joined in {0.joined_at}'.format(member))
#
#@bot.group()
#async def cool(ctx):
#    """Says if a user is cool.
#
#    In reality this just checks if a subcommand is being invoked.
#    """
#    if ctx.invoked_subcommand is None:
#        await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))
#
#@cool.command(name='bot')
#async def _bot(ctx):
#    """Is the bot cool?"""
#    await ctx.send('Yes, the bot is cool.')
#
#bot.run(BOT_SECRET_TOKEN)
