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
import numbers

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']

iterations = 10000
fightstylelist = ["Patchwerk", "LightMovement" ,"HeavyMovement", "HecticAddCleave", "HelterSkelter"]
fightstyle = "Patchwerk"
length = 300

#simc verion check
def simc_version():
    versionNum = subprocess.run('%s/simc' %(simcraft_path), shell=True, stdout=subprocess.PIPE)
    return versionNum.stdout.decode('utf-8').strip()   

async def parseOptions(options, channel):
    iters = iterations
    fs = fightstyle
    leng = length
    forced = False
    i = 1
    terminate = False
    while i < len(options):
        if options[i].lower().startswith('it'):
            tmp = options[i].split()
            try:
                if int(puncstrip(tmp[1])) < 25001:
                    iters = int(puncstrip(tmp[1]))
                else:
                    terminate = True
                    await client.send_message(channel, 'Iterations cannot exceed 25000')
            except:
                terminate = True
                await client.send_message(channel, 'Iterations option not passed a number')
        if options[i].lower().startswith('len'):
            tmp = options[i].split()
            try:
                if int(puncstrip(tmp[1])) < 601:
                    leng = int(puncstrip(tmp[1]))
                else:
                    terminate = True
                    await client.send_message(channel, 'Fight Length cannot exceed 600')
            except:
                terminate = True
                await client.send_message(channel, 'Fight Length option not passed a number')
        if options[i].lower().startswith('fig'):
            tmp = options[i].split()
            if tmp[1] in fightstylelist:
                fs = tmp[1]
            else:
                terminate = True
                await client.send_message(channel, 'Unknown fight style. Fight styles can be: ' +
                                          ', '.join(fightstylelist) + '. Please match word exactly.')
        if options[i].lower().startswith('force'):
            forced = True
            await client.send_message(channel, 'Forced acknowledged. Role check will be ignored.')
        i += 1
    return [terminate, iters, fs, leng, forced]

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
    if (tail1.lower() == "eu" or tail1.lower() =="ru"):
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

#Get all the character stats at once
def get_char_info(character, server, region):
    charExists = True
    isDPS = False
    spec = 'Pancake'
    role = 'Waffle'
    statusCode = 200;
    update_time = 'idk';
    try:
        r = requests.get('https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' 
                       % (region, server, character, api_key))
        statusCode = r.status_code
        if(statusCode == 500):
            charExists = False
            return [charExists, statusCode]
        else:
            charExists = True
            update_time = armory_date(r.json())
            isDPS = is_dps(r.json())
            role = get_role(r.json())
            print(role)
            spec = get_spec(r.json())
            return [charExists, statusCode, isDPS, spec, role, update_time]
    except:
        return [False, 400]

#Returns armory update time
def armory_date(armory_json):
    update_time = armory_json['lastModified']
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(update_time / 1000))

#Returns true if DPS role, false if any other role
def is_dps(armory_json):
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
def get_role(armory_json):
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['role']
            if(x):
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
def get_spec(armory_json):
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['name']
            if(x):
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
    if message.content.startswith('!options'):
        await client.send_message(message.channel, 'Options are:\n--force (ignore roles).\n--iterations NUMBER (set num '
                                  'of iterations maximum of 25,000.\n--fightstyle type (set fight type: Patchwerk, LightMovement '
                                  'HeavyMovement, HecticAddCleave or HelterSkelter).\n--lenth NUMBER (fight length, max 600).\n'
                                  'Example of how to use: !sim Character-Realm-Region --iterations 12500 --fightstyle LightMovement '
                                  '--length 450\nOptions can be in any order, and not all are necessary')
    if message.content.startswith('!help'):
        await client.send_message(message.channel, 'To simulate: \'!sim charactername-servername-region\'. Only '
                                  'US/EU supported. Sims take a few minutes depending on load. You will get a '
                                  'message when it is completed. For additional options do !options')
        await client.send_message(message.channel, 'Character data is pulled from the Armory, so it may not '
                                  'always be up to date. Please leave in spaces for realm name')
    if message.content.startswith('!nerd') or message.content.startswith('!about'):
        version = simc_version()
        await client.send_message(message.channel, 'I do very basic 10k sims for a Patchwerk fight, using the '
                                  'talents and gear you last logged out in. Custom sims are not available. '
                                  'If a completely custom sim is of interest to you, go sim yourself!')
        await client.send_message(message.channel, 'I run %s. The Bot itself was forked from Simbot 0.9' % 
                                 (version))
        await client.send_message(message.channel, 'I run on a 4 core cloud VPS hosted on linode. Even with '
                                  '4 cores, I am sometimes slow- because simcraft is a CPU hog. Interested '
                                  'in your own VPS? Feel free to use our referral code: '
                                  'https://www.linode.com/?r=9d48802831815c3edba8abb1431f3ade33ef357d (we get a '
                                  '$20 credit if you stay for 90 days)')
    if message.content.startswith('!version'):
        version = simc_version()
        await client.send_message(message.channel, 'I run %s.'(version))
    if (message.content.startswith('!2sim ') or message.content.startswith('!3sim ') or 
        message.content.startswith('!sim3 ') or message.content.startswith('!sim ') or 
        message.content.startswith('!dps ')):
        run2 = False
        run3 = False
        runAll3 = False
        runStandalone = False
        runDPS = False
        inputMessage = message.content.split(' --')
        iters = iterations
        fightType = fightstyle
        runtime = length
        force = False
        if len(inputMessage) > 1:
            getOptions = await parseOptions(inputMessage, message.channel)
            if getOptions[0]:
                return
            iters = getOptions[1]
            fightType = getOptions[2]
            runtime = getOptions[3]
            force = getOptions[4]

        if(message.content.startswith('!2sim ')):
            character = charstrip(inputMessage[0], '!2sim ').strip()
            run2 = True
        elif(message.content.startswith('!3sim ')):
            character = charstrip(inputMessage[0], '!3sim ').strip()
            run3 = True
        elif(message.content.startswith('!sim3 ')):
            character = charstrip(inputMessage[0], '!sim3 ').strip()
            runAll3 = True
        elif(message.content.startswith('!sim ')):
            character = charstrip(inputMessage[0], '!sim ').strip()
            runStandalone = True
        elif(message.content.startswith('!dps ')):
            character = charstrip(inputMessage[0], '!dps ').strip()
            runDPS = True
        server = serverstrip(inputMessage[0]).replace("'", "").strip()
        region = regionfind(inputMessage[0]).strip()
        escapeAuthor = author.mention.replace(">", "\>").replace("<", "\<")        
        print('Looking at %s - %s - %s' % (character, server, region))
        await client.send_message(message.channel, 'I take about 2 minutes to run a sim, but concurrent '
                                  'simulations will slow me down! Be gentle... I\'m delicate :^)\nLooking '
                                  'up %s - %s - %s.' % (character, server, region))                    
        #get char info returns as: CharExists, Status Code, isDPS, Spec, Role, update time
        charInfo = get_char_info(character, server, region)
        toonExists = charInfo[0]
        if toonExists:
            print("Toon exists, moving on")
            isDPS = charInfo[2]
            spec = charInfo[3]
            role = charInfo[4]
            armory_date = charInfo[5]
            print('Looking at %s - %s - %s who exists and is a %s' % (character, server, region, spec ))
            if (isDPS or spec == 'Shadow' or force):
                await client.send_message(message.channel, 'Current spec for %s-%s-%s: %s. Armory info last '
                                          'updated %s' % (character, server, region, spec, armory_date))
                if(run2):
                    print('Starting a 2 target standalone')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 2 yes True %s %s %s' % (character, server, 
                                     message.channel.id, escapeAuthor, region, iters, fightType, runtime), shell=True)
                elif(run3):
                    print('Starting a 3 target standalone')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 3 yes True %s %s %s' % (character, server, 
                                      message.channel.id, escapeAuthor, region, iters, fightType, runtime), shell=True)
                elif(runAll3):
                    print('Starting the 1,2,3 sim run')
                    await client.send_message(message.channel, 'Starting 3 sims for 1, 2 and 3 targets for '
                                              '%s - %s - %s. These will run one after the other and will '
                                              'take several minutes.' % (character, server, region))
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 1 no True %s %s %s' % (character, server, 
                                     message.channel.id, escapeAuthor, region, iters, fightType, runtime), shell=True)
                elif(runStandalone):
                    print('Starting a 1 target standalone')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes True %s %s %s' % (character, server, 
                                      message.channel.id, escapeAuthor, region, iters, fightType, runtime), shell=True)
                elif(runDPS):
                    print('Starting DPS only')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes False %s %s %s' % (character, server, 
                                     message.channel.id, escapeAuthor, region, iters, fightType, runtime), shell=True)
                else:
                    #Failsafe is single sim
                    print('I shouldn\'t be here, but gonna run a single target sim')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes True %s %s %s' % (character, server, 
                                     message.channel. id, escapeAuthor, region, iters, fightType, runtime), shell=True)
            else:
                if (role == 'TANK'):
                    await client.send_message(message.channel, 'Sims don\'t work well for tanks, therefore '
                                              'tank sims are limited to DPS only')
                    await client.send_message(message.channel, 'Current spec for %s-%s-%s: %s. Armory info '
                                              'last updated %s' % (character, server, region, spec, 
                                              armory_date))
                    await client.send_message(message.channel, 'Starting DPS only sim, I will ping you when '
                                              'I\'m done')
                    subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes False %s %s %s' % (character, server, message.channel.id, 
                                     escapeAuthor, region, iters, fightType, runtime), shell=True)
                elif (role == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. '
                                                  'This is a limitation of SimulationCraft.' % author.mention)
                else:
                    await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. '
                                              'Make sure your format is \'!sim charactername-servername-region\'.'
                                              % (author.mention, character, server, region))
        else:
            code = charInfo[1]
            print(code)
            if (code == 404):
                await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your format '
                                           'is \'!sim charactername-servername-region\'. Multiple failures here '
                                           'indicate a problem accessing Blizzard\'s API' % (author.mention, 
                                           character, server, region))
            elif (code == 500):
                await client.send_message(message.channel, '%s: Character %s-%s-%s and Blizzard\'s API are not '
                                          'getting along. SimC is unavailble for this toon, and cannot run. '
                                          'I\'m so sorry' % (author.mention, character, server, region))
            elif (code == 400):
                await client.send_message(message.channel, '%s: Error getting info for character %s-%s-%s. Make sure '
                                          'your format is \'!sim charactername-servername-region\'.' % 
                                          (author.mention, character, server, region))
            else:
                await client.send_message(message.channel, '%s: Character %s-%s-%s not found. Make sure your '
                                          'format is \'!sim charactername-servername-region\'. Multiple failures '
                                          'here indicate a problem accessing Blizzard\'s API' % (author.mention, 
                                          character, server, region))

client.run(token)
