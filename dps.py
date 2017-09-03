import subprocess
import sys
import discord
import json
from bs4 import BeautifulSoup
import re
import os
import datetime
import time

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']
character = str(sys.argv[1])
server = str(sys.argv[2])
channel = str(sys.argv[3])
author = sys.argv[4]
region = str(sys.argv[5])
time = str(int(time.time()))
pawn = "Pawn strips from DFS sims are not generated because they do not use scaling in the sim"
dps = ""


def damagestrip(character, server, region):
    global dps;
    try:  
        with open('%s%s-%s-%s-dps-%s.html' % (simcraft_path, character, server, region, time), encoding='utf8') as infile:
            soup = BeautifulSoup(infile, "html.parser")
            dps = soup.find(text=re.compile(' dps')).strip()
            return soup.find(text=re.compile(' dps'))
    except:
        dps = "Bad sim, no DPS"
        print('Bad sim, cannot find %s%s-%s-%s-dps-%s.html' % (simcraft_path, character, server, region, time))
        #subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes' % (character, server, channel, escapeAuthor, region), shell=True)
        return 'Error simming character, simcraft crashed during sim. Please try again'

    
def mod_date(filename):
    try:
        t = os.path.getmtime(filename)
        return datetime.datetime.fromtimestamp(t)
    except:
        return 'Error'

def generateurl():
    try:
        print("%smakesimcsummary.sh %s %s %s '%s' '%s' %s%s-%s-%s-dps-%s.html %s" % (simcraft_path, character, server,  region, dps, pawn,  simcraft_path, character, server, region, time, simcraft_path))
        filename = subprocess.run("%smakesimcsummary.sh %s %s %s '%s' '%s' %s%s-%s-%s-dps-%s.html %s" % (simcraft_path, character, server,  region, dps, pawn, simcraft_path, character, server, region, time, simcraft_path), shell=True, stdout=subprocess.PIPE)
        return ('http://www.ketbots.com/sims/%s' % filename.stdout.decode('utf-8').strip())
    except:
        return 'Unable to move file to www.ketbots.com'


@client.event
async def on_ready():
        for x in config_json['servers']:
            client.accept_invite(x)
        await client.send_message(client.get_channel(channel), 'DPS simulation on %s completed.' % (character))
        await client.send_message(client.get_channel(channel), '%s: %s' % (author, damagestrip(character, server, region)))
        await client.send_message(client.get_channel(channel), 'View detailed results for %s here: %s' % (character, generateurl()))
        await client.logout()

print('%s./simc armory=%s,%s,%s calculate_scale_factors=0 iterations=10000 html=%s-%s-%s-dps-%s.html output=%s-%s-%s.txt fight_style=LightMovement' % (simcraft_path, region, server, character, character, server, region, time,  character, region, time))
subprocess.call('%s./simc armory=%s,%s,%s calculate_scale_factors=0 iterations=10000 html=%s-%s-%s-dps-%s.html output=%s-%s-%s.txt fight_style=LightMovement' % (simcraft_path, region, server, character, character, server, region, time, character, region, time), cwd=simcraft_path, shell=True)
client.run(token)
