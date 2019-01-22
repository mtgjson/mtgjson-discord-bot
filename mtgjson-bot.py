#!/usr/bin/python
import discord
import asyncio
import MySQLdb

DATABASE_HOST = 'localhost'
DATABASE_USER = 'user'
DATABASE_PASSWD = 'passwd'
DATABASE_NAME = 'db'
BOT_SECRET = 'token'

try:
   from config import *
except ImportError:
   pass

db = MySQLdb.connect(host=DATABASE_HOST,    # your host, usually localhost
                     user=DATABASE_USER,         # your username
                     passwd=DATABASE_PASSWD,  # your password
                     db=DATABASE_NAME)        # name of the database

cur = db.cursor()

client = discord.Client()

@client.event
@asyncio.coroutine on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
@asyncio.coroutine on_message(message):
    if message.content.startswith('!test'):
        counter = 0
        tmp = yield from client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        yield from client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        yield from asyncio.sleep(5)
        yield from client.send_message(message.channel, 'Done sleeping')

client.run(BOT_SECRET)