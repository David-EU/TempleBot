import discord
import json
import subprocess
import os
import datetime
import requests
import re
from string import punctuation
from bs4 import BeautifulSoup
import time

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']

#Returns true if character exists on armory, false otherwise
def char_exists(character,server, region):    
    try:
        print('https://%s.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (region, server, character, api_key))
        requests.get('https://%s.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (region, server, character, api_key))
        return True
    except:
        return False

#Removes strip from message, and returns Charactername in a message formatted 'charactername-servername'
def charstrip(message, strip):
    character = message.replace("%s" % strip, "")
    head, sep, tail = character.partition('-')
    head = puncstrip(head)
    return head.capitalize()

#Returns Servername from '!command charactername-servername' input
def serverstrip(message):
    head, sep, tail = message.partition('-')
    head1, sep1, tail1 = tail.partition('-')
    return head1.capitalize().strip().replace(" ", "-")

#Returns Servername from '!command charactername-servername' input
def regionfind(message):
    head, sep, tail = message.partition('-')
    head1, sep1, tail1 = tail.partition('-')
    region = tail1.lower();
    if (tail1.lower() == "us" or tail1.lower() =="na"):
        region = "us";
    if (tail1.lower() == "eu"):
        region = "eu";
    return region;

#Returns s stripped of all punctuation
def puncstrip(s):
    return ''.join(c for c in s if c not in punctuation)

#Returns a pawn string from simcraft output
def pawnstrip(character, server):
    with open('%s%s-%s.html' % (simcraft_path, character, server), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' Pawn: v1: '))

#Returns modified date of a file in local time        
def mod_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

#Returns armory update time
def armory_date(character, server, region):
    print('https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (region, server, character, api_key))
    armory_json = requests.get('https://%s.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (region, server, character, api_key))
    armory_json = armory_json.json()
    update_time = armory_json['lastModified']
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(update_time / 1000))

#Returns true if DPS role, false if any other role
def is_dps(character, server, region):
    armory_json = requests.get('https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (region, server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            armory_json['talents'][0]['talents'][i]['spec']['role'] == 'DPS'
            return armory_json['talents'][0]['talents'][i]['spec']['role'] == 'DPS'
        except:
            print('No role (isDPS check 1 ) identifier in tier %s.' % i)
    print('Can\'t find first try, going second')
    for i in range(0,7):
        try:
            selected = armory_json['talents'][i]['selected']
            if(selected):
                return armory_json['talents'][i]['talents'][i]['spec']['role']  == 'DPS'
        except:
            print('No role (isDPS check 2 ) identifier in tier %s.' % i)
    print('Making 3rd and final attempt to get isDPS')
    for i in range(0,7):
        try:
            selected = armory_json['talents'][i]['selected']
            if(selected):
                return armory_json['talents'][i]['spec']['name'] == 'DPS'      
        except:
            print('No role (isDPS check 3 ) identifier in tier %s.' % i)

#Returns role            
def get_role(character, server, region):
    armory_json = requests.get('https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (region, server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['role']
            return x
        except:
            print('No role (getrole 1) identifier in tier %s.' % i)
    print('Can\'t find role (getRole check1), going second')
    for i in range(0,7):
        try:
            selected = armory_json['talents'][i]['selected']
            if(selected):
                return armory_json['talents'][i]['talents'][i]['spec']['role']
        except:
            print('No role (getrole 2) identifier in tier %s.' % i)
    print("3rd and final attempt to get Role")
    for i in range(0,7):
        try:
            x = armory_json['talents'][i]['spec']['role']  
            return x
        except:
            print('No role (getrole 3) identifier in tier %s.' % i)

#Returns spec    
def get_spec(character, server, region):
    armory_json = requests.get('https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (region, server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['name']
            return x
        except:
            print('No spec (getspec 1) identifier in tier %s.' % i)
    print('Can\'t find spec (getSpec check1), going second')
    for i in range(0,3):
        try:
            selected = armory_json['talents'][i]['selected']
            if(selected):
                x = armory_json['talents'][i]['talents'][i]['spec']['name']        
                return x
        except:
            print('No spec (getspec 2) identifier in tier %s.' % i)
    print('3rd and final attempt to getSpec')
    for i in range(0,3):
        try:
            selected = armory_json['talents'][i]['selected']
            if(selected):
                x = armory_json['talents'][i]['spec']['name']        
                return x
        except:
            print('No spec3 identifier in tier %s.' % i)

@client.event
async def on_ready():
#On ready, joins all servers in JSON
    for x in config_json['servers']:
        client.accept_invite(x)
    print('Logged in as')
    print(client.user.name)
    print('---------')
    
@client.event
async def on_message(message):
    author = message.author
    if message.content.startswith('!sim '):
        character = charstrip(message.content, '!sim ').strip()
        server = serverstrip(message.content).replace("'", "").strip()
        region = regionfind(message.content).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        if char_exists(character, server, region):
            print("Toon exists, moving on")
            isDPS = is_dps(character, server, region)
            spec = get_spec(character, server, region)
            role = get_role(character, server, region)
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow'):
                if(spec == 'Shadow' or True):
                    await client.send_message(message.channel, 'Pulling simming stats for %s - %s - %s. Be aware concurrent simulations will slow me down. Be gentle... I\'m delicate :^)' % (character, server, region))
                    await client.send_message(message.channel, 'Temple Bot takes about 3-5 min to run a sim (longer if multiple sims are going at the same time). I will ping you when I\'m done')
                    await client.send_message(message.channel, 'Current spec: %s. Armory info last updated %s' % (spec, armory_date(character, server, region)))                
                    await client.send_message(message.channel, '%s: Starting sim. This will take several minutes.' % author.mention)                
                    subprocess.Popen('python3 sim.py %s %s %s %s %s' % (character, server, message.channel.id, escapeAuthor, region), shell=True)
                else:
                    await client.send_message(message.channel, '%s: Sorry, I am a mean temple bot. I only have eyes for Shadow Priests.' % author.mention)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, '%s: Sorry, sims for pawn do not work well for Tanks. This is a limitation of SimulationCraft. Have you thought about being Shadow? I like Shadow' % author.mention)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft. Have you thought about being Shadow?' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Role not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))
        else:
            await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))    
    if message.content.startswith('!help'):
        await client.send_message(message.channel, 'To simulate: \'!sim charactername-servername-region\'. Only US/EU supported. Sims take a few minutes depending on load. You will get a message when it is completed.')    
        await client.send_message(message.channel, 'Character data is pulled from the Armory, so it may not always be up to date. Please leave in spaces for realm name')
    if message.content.startswith('!nerd'):
        await client.send_message(message.channel, 'I do very basic 10k sims for a Patchwerk fight, using the talents and gear you last logged out in. Custom sims are not available. If a completely custom sim is of interest to you, go sim yourself!')
        await client.send_message(message.channel, 'Temple Bot runs SimulationCraft 715-01 for World of Warcraft 7.1.5 Live (wow build 23360, git build c8f3bd3). Temple Bot runs a modified Simbot 0.9.')
        await client.send_message(message.channel, 'Temple Bot runs on a 3 year old computer. Temple Bot is slow. Temple Bot thought it was in retirement. Temple Bot was wrong.')
    if message.content.startswith('!dps '):
        character = charstrip(message.content, '!dps ').strip()
        server = serverstrip(message.content).replace("'", "").strip()
        region = regionfind(message.content).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        if char_exists(character, server, region):
            print("Toon exists, moving on")
            isDPS = is_dps(character, server, region)
            spec = get_spec(character, server, region)
            role = get_role(character, server, region)
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow'):
                if(spec == 'Shadow' or trues):
                    await client.send_message(message.channel, 'Pulling dps stats for %s - %s - %s. Be aware concurrent simulations will slow me down. Be gentle... I\'m delicate :^)' % (character, server, region))
                    await client.send_message(message.channel, 'Temple Bot takes about 3-5 min to run a sim (longer if multiple sims are going at the same time). I will ping you when I\'m done')
                    await client.send_message(message.channel, 'Current spec: %s. Armory info last updated %s' % (spec, armory_date(character, server, region)))                
                    await client.send_message(message.channel, '%s: Starting sim. This will take several minutes.' % author.mention)                
                    subprocess.Popen('python3 dps.py %s %s %s %s %s' % (character, server, message.channel.id, escapeAuthor, region), shell=True)
                else:
                    await client.send_message(message.channel, '%s: Sorry, I am a mean temple bot. I only have eyes for Shadow Priests.' % author.mention)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, '%s: Sorry, sims for pawn do not work well for Tanks. This is a limitation of SimulationCraft. Have you thought about being Shadow? I like Shadow' % author.mention)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft. Have you thought about being Shadow?' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Role not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))
        else:
            await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))    
    if message.content.startswith('!sim3 '):
        character = charstrip(message.content, '!sim3 ').strip()
        server = serverstrip(message.content).replace("'", "").strip()
        region = regionfind(message.content).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        if char_exists(character, server, region):
            print("Toon exists, moving on")
            isDPS = is_dps(character, server, region)
            spec = get_spec(character, server, region)
            role = get_role(character, server, region)
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow'):
                if(spec == 'Shadow'):
                    await client.send_message(message.channel, 'Pulling simming stats for %s - %s - %s. Be aware concurrent simulations will slow me down. Be gentle... I\'m delicate :^)' % (character, server, region))
                    await client.send_message(message.channel, 'Temple Bot takes about 3-5 min to run a sim (longer if multiple sims are going at the same time). I will ping you when I\'m done')
                    await client.send_message(message.channel, 'Current spec: %s. Armory info last updated %s' % (spec, armory_date(character, server, region)))                
                    await client.send_message(message.channel, '%s: Starting 3 sims for 1, 2 and 3 targets. These will run one after the other and will take several minutes.' % author.mention)               
                    subprocess.Popen('python3 sim1.py %s %s %s %s %s' % (character, server, message.channel.id, escapeAuthor, region), shell=True)
                else:
                    await client.send_message(message.channel, '%s: Sorry, I am a mean temple bot. I only have eyes for Shadow Priests.' % author.mention)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, '%s: Sorry, sims for pawn do not work well for Tanks. This is a limitation of SimulationCraft. Have you thought about being Shadow? I like Shadow' % author.mention)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft. Have you thought about being Shadow?' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Role not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))
        else:
            await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))    
    if message.content.startswith('!2sim '):
        character = charstrip(message.content, '!2sim ').strip()
        server = serverstrip(message.content).replace("'", "").strip()
        region = regionfind(message.content).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        if char_exists(character, server, region):
            print("Toon exists, moving on")
            isDPS = is_dps(character, server, region)
            spec = get_spec(character, server, region)
            role = get_role(character, server, region)
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow'):
                if(spec == 'Shadow'):
                    await client.send_message(message.channel, 'Pulling simming stats for %s - %s - %s. Be aware concurrent simulations will slow me down. Be gentle... I\'m delicate :^)' % (character, server, region))
                    await client.send_message(message.channel, 'Temple Bot takes about 3-5 min to run a sim (longer if multiple sims are going at the same time). I will ping you when I\'m done')
                    await client.send_message(message.channel, 'Current spec: %s. Armory info last updated %s' % (spec, armory_date(character, server, region)))                
                    await client.send_message(message.channel, '%s: Starting 1 sim for 2 targets. This will take several minutes.' % author.mention)               
                    subprocess.Popen('python3 sim2.py %s %s %s %s %s yes' % (character, server, message.channel.id, escapeAuthor, region), shell=True)
                else:
                    await client.send_message(message.channel, '%s: Sorry, I am a mean temple bot. I only have eyes for Shadow Priests.' % author.mention)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, '%s: Sorry, sims for pawn do not work well for Tanks. This is a limitation of SimulationCraft. Have you thought about being Shadow? I like Shadow' % author.mention)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft. Have you thought about being Shadow?' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Role not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))
        else:
            await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))    
    if message.content.startswith('!3sim '):
        character = charstrip(message.content, '!3sim ').strip()
        server = serverstrip(message.content).replace("'", "").strip()
        region = regionfind(message.content).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        if char_exists(character, server, region):
            print("Toon exists, moving on")
            isDPS = is_dps(character, server, region)
            spec = get_spec(character, server, region)
            role = get_role(character, server, region)
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow'):
                if(spec == 'Shadow'):
                    await client.send_message(message.channel, 'Pulling simming stats for %s - %s - %s. Be aware concurrent simulations will slow me down. Be gentle... I\'m delicate :^)' % (character, server, region))
                    await client.send_message(message.channel, 'Temple Bot takes about 3-5 min to run a sim (longer if multiple sims are going at the same time). I will ping you when I\'m done')
                    await client.send_message(message.channel, 'Current spec: %s. Armory info last updated %s' % (spec, armory_date(character, server, region)))                
                    await client.send_message(message.channel, '%s: Starting  1 sim for 3 targets. This will take several minutes.' % author.mention)               
                    subprocess.Popen('python3 sim3.py %s %s %s %s %s yes' % (character, server, message.channel.id, escapeAuthor, region), shell=True)
                else:
                    await client.send_message(message.channel, '%s: Sorry, I am a mean temple bot. I only have eyes for Shadow Priests.' % author.mention)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, '%s: Sorry, sims for pawn do not work well for Tanks. This is a limitation of SimulationCraft. Have you thought about being Shadow? I like Shadow' % author.mention)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft. Have you thought about being Shadow?' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Role not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))
        else:
            await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format is \'!sim charactername-servername-region\'.' % (author.mention, character, server, region))    

client.run(token)
