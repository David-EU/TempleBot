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
numberTargets = str(sys.argv[6])
escapeAuthor = str(sys.argv[4]).replace(">", "\>").replace("<", "\<")
standAlone = str(sys.argv[7])

def pawnstrip(character, server, region, numberTargets, standAlone):
    try:
        with open('%s%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets), encoding='utf8') as infile:
            soup = BeautifulSoup(infile, "html.parser")
            if(numberTargets == '1' ):
                return soup.find(text=re.compile(' Pawn: v1: '))
            elif(numberTargets == '2' ):
                return soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 2 Target")
            elif(numberTargets == '3' ):
                return soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 3 Target")
            else:
                print("Something's not quite right. Default pawn print")
                return soup.find(text=re.compile(' Pawn: v1: '))
    except:
        print('Bad sim, cannot find %s%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets))
        return 'Error simming character, simcraft crashed during sim. Please try again'
    
def damagestrip(character, server, region, numberTargets):
    with open('%s%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' dps'))

def mod_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

@client.event
async def on_ready():
        for x in config_json['servers']:
            client.accept_invite(x)
        await client.send_message(client.get_channel(channel), '%s: Stat weight simulation on %s completed. This is for a %a target fight' % (author, character, numberTargets))
        await client.send_message(client.get_channel(channel), '%s: Remember, this is for %s\'s current talents! Other talent combos will likely be a different pawn string.' % (author, character))
        await client.send_message(client.get_channel(channel), '%s: %s' % (author, pawnstrip(character, server, region, numberTargets, standAlone)))
        #await client.send_message(client.get_channel(channel), '%s: %s' % (author, damagestrip(character, server, region, numberTargets)))
        if(numberTargets == '1' and standAlone == "no"):
            await client.send_message(client.get_channel(channel), 'Starting 2 target sim')                    
            subprocess.Popen('python3 sim.py %s %s %s %s %s 2 no' % (character, server, channel, escapeAuthor, region), shell=True)
        elif(numberTargets == '2' and standAlone == "no"):
            await client.send_message(client.get_channel(channel), 'Starting 3 target sim')                    
            subprocess.Popen('python3 sim.py %s %s %s %s %s 3 no' % (character, server, channel, escapeAuthor, region), shell=True)
        elif(numberTargets == '3' and standAlone == "no"):
            await client.send_message(client.get_channel(channel), 'Does a 2 or 3 target look majorly off? Rerun a 2 target using !2sim character-server-region. Rerun a 3 with !3sim character-server-region')          
        await client.logout()
print('Starting sim:')
print('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=intellect,crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 desired_targets=%s html=%s-%s-%s-%s.html output=%s-%s-%s.txt' % (simcraft_path, region, server, character, numberTargets, character, server, region, numberTargets, character, region, numberTargets))
subprocess.call('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=intellect,crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 desired_targets=%s html=%s-%s-%s-%s.html output=%s-%s-%s.txt' % (simcraft_path, region, server, character, numberTargets, character, server, region, numberTargets, character, region, numberTargets), cwd=simcraft_path, shell=True)
client.run(token)