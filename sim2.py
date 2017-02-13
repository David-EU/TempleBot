import subprocess
import sys
import json
import discord
from bs4 import BeautifulSoup
import re
import os
import datetime

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']
character = str(sys.argv[1])
server = str(sys.argv[2])
channel = str(sys.argv[3])
author = str(sys.argv[4])
region = str(sys.argv[5])
escapeAuthor = str(sys.argv[4]).replace(">", "\>").replace("<", "\<")
standAlone = str(sys.argv[6])

def pawnstrip(character, server, region):
    try:
        with open('%s%s-%s-%s-2.html' % (simcraft_path, character, server, region), encoding='utf8') as infile:
            soup = BeautifulSoup(infile, "html.parser")
            return soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 2 Target")
    except:
        print('Bad sim, cannot find %s%s-%s-%s-2.html' % (simcraft_path, character, server, region))
        return 'Error simming character, simcraft crashed during sim. Please try again'
    
    
def mod_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

@client.event
async def on_ready():
        for x in config_json['servers']:
            client.accept_invite(x)
        await client.send_message(client.get_channel(channel), '%s: Stat weight simulation on %s completed. This is for 2 targets' % (author, character))
        await client.send_message(client.get_channel(channel), '%s: Remember, this is for %s\'s current talents! Other talent combos will likely be a different pawn string.' % (author, character))
        await client.send_message(client.get_channel(channel), '%s: %s' % (author, pawnstrip(character, server, region)))
        if(standAlone == "no"):
            await client.send_message(client.get_channel(channel), 'Starting 3 target sim')                    
            subprocess.Popen('python3 sim3.py %s %s %s %s %s no' % (character, server, channel, escapeAuthor, region), shell=True)
        await client.logout()
print('Starting sim:')
print('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=intellect,crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 html=%s-%s-%s-2.html output=%s-%s-2.txt' % (simcraft_path, region, server, character, character, server, region, character, region))
subprocess.call('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=intellect,crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 desired_targets=2 html=%s-%s-%s-2.html output=%s-%s-2.txt' % (simcraft_path, region, server, character, character, server, region, character, region), cwd=simcraft_path, shell=True)
client.run(token)