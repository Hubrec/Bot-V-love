import discord
import os
from discord.ext import commands
import random
from dotenv import load_dotenv

load_dotenv()

# Bot Prefix

description = '''
        Bot Prefix : !
        Bot Commands : ping
        Bot Description : A simple bot that replies to ping.
        '''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', case_insensitive=True, description=description, intents=intents)

# Api velov requests / data fetching every minutes

import urllib3
import json

http = urllib3.PoolManager()

def liste_stations_ville(ville) :
    url = "https://api.jcdecaux.com/vls/v3/stations?contract="+ville+"&apiKey="+os.getenv('API_KEY')
    r = http.request('GET', url)
    l = json.loads(r.data)
    return l

l = liste_stations_ville("lyon")

listeData = []

for k in l:
    tmp = {"numero": k['number'],
        "nbVelo": k["totalStands"]["availabilities"]["bikes"],
        "nbPlace": k["totalStands"]["availabilities"]["stands"],
        "nom": k["name"], 
        "longitude": k["position"]["longitude"],
        "latitude": k["position"]["latitude"]
        }
    if " - " in tmp["nom"] :
        tmp["nom"] = tmp["nom"].split(" - ")[1]
    listeData.append(tmp)

listeData.sort(key=lambda x: x["numero"])

# Bot Startup

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

# Bot Commands

RED = color=discord.Color.red()

# simple ping command
@bot.command()
async def ping(ctx):
    await ctx.send('Pong ! ')

# help command
@bot.command()
async def aide(ctx):
    await ctx.send('Voici les commandes disponibles : ')
    await ctx.send('!ping : renvoie pong')
    await ctx.send('!all <INT> : renvoie une sous liste du nombre d\'elements mis en paramètres des stations velov de lyon aléatoire')
    await ctx.send('!station <STRING> : renvoie les informations d\'une station velov de lyon avec un mot pour selectionner une station')

# all command that returns a list of velov stations
@bot.command()
async def all(ctx, arg):
    cpt = 0
    arg = int(arg)
    random.shuffle(listeData)
    embed = discord.Embed(title="Liste des stations", color=RED)
    for k in listeData :
        embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
        cpt += 1
        if cpt >= arg: 
            break
    await ctx.send(embed = embed)

# station command that returns the information of a specific velov station
@bot.command()
async def station(ctx, arg):
    arg = str(arg).upper()
    found = False
    listeData.sort(key=lambda x: x["numero"])
    for k in listeData :
        if arg in k["nom"]:
            embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"], color=RED)
            embed.add_field(name="*Vélos disponibles*", value=str(k["nbVelo"]), inline=True)
            embed.add_field(name="*Places disponibles*", value=str(k["nbPlace"]), inline=True)
            found = True
            break
    if not found:
        embed = discord.Embed(title="Erreur", description="Aucune station ne correspond à votre recherche", color=RED)
    
    await ctx.send(embed = embed)

# Bot run

bot.run(os.getenv('TOKEN'))