import discord
import os
from discord.ext import commands
import random
from dotenv import load_dotenv
import time

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

clock = int(time.time())

def fetchData():    
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
    return listeData

listeData = fetchData()

def updateData():
    global clock
    if int(time.time()) - clock >= 60:
        clock = int(time.time())
        return fetchData()
    else:
        return listeData

# Bot Startup

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Bot Commands

RED = color=discord.Color.red()
GREEN = color=discord.Color.green()
BLUE = color=discord.Color.blue()

# simple ping command
@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

# help command
@bot.command()
async def aide(ctx):
    embed = discord.Embed(title="Voici la liste de mes compétences : ", color=RED)
    embed.add_field(name="!aide", value="Affiche la liste des commandes", inline=False)
    embed.add_field(name="!ping", value="Renvoie pong", inline=False)
    embed.add_field(name="!all <INT>", value="Renvoie une sous liste du nombre d'elements mis en paramètres des stations velov de lyon aléatoire", inline=False)
    embed.add_field(name="!station <STRING>", value="Renvoie les informations d'une station velov de lyon avec un mot pour selectionner une station", inline=False)
    await ctx.send(embed = embed)

# all command that returns a list of velov stations
@bot.command()
async def all(ctx, arg):
    listeData = updateData()
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
async def station(ctx, arg, arg2=None, arg3=None, arg4=None):
    listeData = updateData()
    if arg2 is not None:
        arg += " " + arg2
        if arg3 is not None:
            arg += " " + arg3
            if arg4 is not None:
                arg += " " + arg4
    arg = str(arg).upper()
    found = False
    listeData.sort(key=lambda x: x["numero"])
    for k in listeData :
        if arg in k["nom"]:
            embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"])
            if (k["nbVelo"] == 0):
                embed.set_thumbnail(url="https://ibb.co/1Zz80Sm")
            elif (k["nbPlace"] == 0):
                embed.set_thumbnail(url="https://ibb.co/nc2YsrL")
            else:
                embed.set_thumbnail(url="https://ibb.co/xqMM32H")
            embed.add_field(name="*Vélos disponibles*", value=str(k["nbVelo"]), inline=True)
            embed.add_field(name="*Places disponibles*", value=str(k["nbPlace"]), inline=True)
            found = True
            break
    if not found:
        embed = discord.Embed(title="Erreur", description="Aucune station ne correspond à votre recherche", color=RED)
    
    await ctx.send(embed = embed)

@bot.command()
async def embed(ctx):

    embed=discord.Embed(

    title="Text Formatting",
        url="https://realdrewdata.medium.com/",
        description="Here are some ways to format text",
        color=discord.Color.red())
    
    embed.set_author(name="RealDrewData", url="https://twitter.com/RealDrewData", icon_url="https://cdn-images-1.medium.com/fit/c/32/32/1*QVYjh50XJuOLQBeH_RZoGw.jpeg")
    embed.set_thumbnail(url="https://i.imgur.com/axLm3p6.jpeg")
    embed.add_field(name="*Italics*", value="Surround your text in asterisks (\*)", inline=False)
    embed.add_field(name="**Bold**", value="Surround your text in double asterisks (\*\*)", inline=False)
    embed.add_field(name="__Underline__", value="Surround your text in double underscores (\_\_)", inline=False)
    embed.add_field(name="~~Strikethrough~~", value="Surround your text in double tildes (\~\~)", inline=False)
    embed.add_field(name="`Code Chunks`", value="Surround your text in backticks (\`)", inline=False)
    embed.add_field(name="Blockquotes", value="> Start your text with a greater than symbol (\>)", inline=False)
    embed.add_field(name="Secrets", value="||Surround your text with double pipes (\|\|)||", inline=False)
    embed.set_footer(text="Learn more here: realdrewdata.medium.com")

    await ctx.send(embed=embed)

# Bot run

bot.run(os.getenv('TOKEN'))