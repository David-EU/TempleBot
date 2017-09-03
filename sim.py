import subprocess
import sys
import json
import discord
from bs4 import BeautifulSoup
import re
import os
import datetime
import time
import asyncio

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
time = str(int(time.time()))
pawn = ""
dps = ""

def pawnstrip(character, server, region, numberTargets, standAlone):
    global pawn
    try:
        with open('%s%s-%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets, time), 
                  encoding='utf8') as infile:
            soup = BeautifulSoup(infile, "html.parser")
            if(numberTargets == '1' ):
                pawn = soup.find(text=re.compile(' Pawn: v1: ')).strip()
                return soup.find(text=re.compile(' Pawn: v1: '))
            elif(numberTargets == '2' ):
                pawn = soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 2 Target").strip()
                return soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 2 Target")
            elif(numberTargets == '3' ):
                pawn = soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 3 Target").strip()
                return soup.find(text=re.compile(' Pawn: v1: ')).replace(character, character + " 3 Target")
            else:
                print("Something's not quite right. Default pawn print")
                pawn = soup.find(text=re.compile(' Pawn: v1: ')).strip()
                return soup.find(text=re.compile(' Pawn: v1: '))
    except:
        pawn = 'Bad sim, no pawn string'
        print('Bad sim, cannot find %s%s-%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets, time))
        #subprocess.Popen('python3 sim.py %s %s %s %s %s 1 yes' % (character, server, channel, escapeAuthor, region), shell=True)
        return 'Error simming character, simcraft crashed during sim. Please try again'
    
def damagestrip(character, server, region, numberTargets):
    global dps
    try:
        with open('%s%s-%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets, time), 
                  encoding='utf8') as infile:
            soup = BeautifulSoup(infile, "html.parser")
            dps = soup.find(text=re.compile(' dps'))
            return soup.find(text=re.compile(' dps'))
    except:
        print('Bad sim, no DPS')
        dps = 'Bad sim, no DPS'
        return 'ERROR: Unable to provide DPS due to crashed sim.'

def generateurl():
    try:
        print("%smakesimcsummary.sh %s %s %s '%s' '%s' %s%s-%s-%s-%s-%s.html %s" % (simcraft_path, character, server, 
              region, dps, pawn,  simcraft_path, character, server, region, numberTargets, time, simcraft_path))
        filename = subprocess.run("%smakesimcsummary.sh %s %s %s '%s' '%s' %s%s-%s-%s-%s-%s.html %s" % (simcraft_path, 
                                  character, server,  region, dps, pawn, simcraft_path, character, server, region, 
                                  numberTargets, time, simcraft_path), shell=True, stdout=subprocess.PIPE)
        return ('http://www.ketbots.com/sims/%s' % filename.stdout.decode('utf-8').strip())
    except:
        return 'Unable to move file to www.ketbots.com'

def fileCleanup():
    try:
        os.remove(os.path.join(simcraft_path, time+ 'simout'))
    except:
        pass
    try:
        os.remove(os.path.join(simcraft_path, time+ 'simerr'))
    except:
        pass
    try:
        os.remove('%s%s-%s-%s-%s-%s.html' % (simcraft_path, character, server, region, numberTargets, time))
    except:
        pass
    try:
        os.remove('%s%s-%s-%s-%s.txt' % (simcraft_path, character, region, numberTargets,time))
    except:
        pass



async def run_sim():
    print('Starting sim:')
    print('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=strength,agility,intellect,crit_rating,'
          'haste_rating,mastery_rating,versatility_rating iterations=10000 desired_targets=%s html=%s-%s-%s-%s-%s.html '
          'output=%s-%s-%s-%s.txt' % (simcraft_path, region, server, character, numberTargets, character, server, region, 
          numberTargets, time, character, region, numberTargets, time))
#The following code was adapted from: https://github.com/stokbaek/simc-discord
    simout = open(os.path.join(simcraft_path, time+ 'simout'), "w")
    simerr = open(os.path.join(simcraft_path, time+'simerr'), "w")
    sim = subprocess.Popen('%s./simc armory=%s,%s,%s calculate_scale_factors=1 scale_only=strength,agility,intellect,'
                           'crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 desired_targets=%s '
                           'html=%s-%s-%s-%s-%s.html output=%s-%s-%s-%s.txt' % (simcraft_path, region, server, character, 
                           numberTargets, character, server, region, numberTargets, time, character, region, numberTargets, 
                           time), cwd=simcraft_path, universal_newlines=True, shell=True, stdout=simout, stderr=simerr)
    progress_message = await client.send_message(client.get_channel(channel), 'Sim Starting')
    await asyncio.sleep(1)
    loop = True
    runTime = 0
    successfulSim = False
    while loop:
        runTime += 2
        if runTime > 6 *60:
            await client.edit_message(progress_message, 'Simulation timed out (6 min) :(')
            sim.terminate()
            
        await asyncio.sleep(1)
        with open(os.path.join(simcraft_path, time+ 'simout'), errors='replace') as s:
            progressCheck = s.readlines()
        with open(os.path.join(simcraft_path, time+'simerr'), errors='replace') as e:
            errors = e.readlines()
        if len(errors) > 0:
            loop = False
            sim.terminate()
            await client.edit_message(progress_message, 'Simulation failed :(\n' + errors)
        else:
            if len(progressCheck) > 1:
                if 'report took' in progressCheck[-2]:
                    loop = False
                    print("sim done")
                    await client.delete_message(progress_message)
                    sim.terminate()
                    successfulSim = True
                else:
                    if 'Generating' in progressCheck[-1]:
                        done ='█' * (20 - progressCheck[-1].count('.'))
                        todo = '░' * (progressCheck[-1].count('.'))
                        progressBar = done + todo
                        percentage = 100 - progressCheck[-1].count('.') * 5 
                        status =  progressCheck[-1].split()[1]
                        if 'sec' in progressCheck[-1].split()[-1] or 'min' in progressCheck[-1].split()[-1]:
                            if 'min' in progressCheck[-1].split()[2]:
                                timer = ' (' + progressCheck[-1].split()[-2] + ' ' + progressCheck[-1].split()[-1] + ' left)'
                            else:
                                timer = ' (' + progressCheck[-1].split()[-1] + ' left)'
                        else:
                            timer = ''
                        try:
                            progress_message = await client.edit_message(progress_message, status + ' ' + progressBar + ' ' + 
                                                                         str(percentage) + '%' + timer)
                            print(status + ' ' + progressBar + ' ' + str(percentage) + '%' + timer) 
                        except:
                            pass
    return successfulSim
#End adapted code

@client.event
async def on_ready():
        success = await run_sim()
        print(success)
        for x in config_json['servers']:
            client.accept_invite(x)
        if success:
            await client.send_message(client.get_channel(channel), 'Stat weight simulation on %s completed. This is for a %a '
                                      'target fight' % (character, numberTargets))
            await client.send_message(client.get_channel(channel), 'Remember, this is for %s\'s current talents! Other talent '
                                      'combos will likely be a different pawn string.' % (character))
            await client.send_message(client.get_channel(channel), '%s: %s' % (author, pawnstrip(character, server, region, 
                                      numberTargets, standAlone)))
            await client.send_message(client.get_channel(channel), '%s' % (damagestrip(character, server, region, numberTargets)))
            await client.send_message(client.get_channel(channel), 'View detailed results for %s here: %s' % (character, 
                                      generateurl()))
            if(numberTargets == '1' and standAlone == "no"):
                await client.send_message(client.get_channel(channel), 'Starting 2 target sim')                    
                subprocess.Popen('python3 sim.py %s %s %s %s %s 2 no' % (character, server, channel, escapeAuthor, region), 
                                 shell=True)
            elif(numberTargets == '2' and standAlone == "no"):
                await client.send_message(client.get_channel(channel), 'Starting 3 target sim')                    
                subprocess.Popen('python3 sim.py %s %s %s %s %s 3 no' % (character, server, channel, escapeAuthor, region), 
                                 shell=True)
            elif(numberTargets == '3' and standAlone == "no"):
                await client.send_message(client.get_channel(channel), 'Does a 2 or 3 target look majorly off? Rerun a 2 target '
                                          'using !2sim character-server-region. Rerun a 3 with !3sim character-server-region')
        else:
            await client.send_message(client.get_channel(channel), 'Simulation failed for %s. Please try again.' % (character))
        fileCleanup()
        await client.logout()

client.run(token)

