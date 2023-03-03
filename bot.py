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
    
# Favorite storage

favorite = []

def addToFavorite(station):
    if (station not in favorite):
        favorite.append(station)
        return True
    else :
        return False

def removeFromFavorite(station):
    if (station in favorite):
        favorite.remove(station)
        return True
    else :
        return False

# Velovs Data Calculs

def totalVelovs(data):
    total = 0
    for k in data:
        total += k["nbVelo"]
    return total

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
    embed = discord.Embed(title="Voici la liste de mes compétences : ", color=BLUE)
    embed.add_field(name="!ping", value="Je réponds pong!", inline=False)
    embed.add_field(name="!aide", value="Je vous envoie cette liste", inline=False)
    embed.add_field(name="!total", value="Je vous envoie le nombre total de vélos disponibles", inline=False)
    embed.add_field(name="!all", value="Je vous envoie une liste de 20 stations aléatoires", inline=False)
    embed.add_field(name="!rand <INT>", value="Je vous envoie <INT> (max 20) station aléatoire", inline=False)
    embed.add_field(name="!station <STRING>", value="Je recherche les stations correspondant a votre recherche et vous renvoie leurs informations (max 5)", inline=False)
    embed.add_field(name="!add <STRING>", value="J'ajoute la station correspondant à votre recherche à vos favoris", inline=False)
    embed.add_field(name="!remove <STRING>", value="Je retire la station correspondant à votre recherche de vos favoris", inline=False)
    embed.add_field(name="!fav", value="Je vous envoie les informations de vos stations favorites", inline=False)
    embed.add_field(name="!update", value="Je vous renvoi un panneau d'informations de l'état du réseau et *refresh* les données (fait automatiquement toutes les 60 secondes)", inline=False)

    await ctx.send(embed = embed)

# all command that returns a list of velov stations
@bot.command()
async def rand(ctx, arg):
    listeData = updateData()
    cpt = 0
    arg = int(arg)
    if (arg > 20):
        arg = 20
    title = "Liste des " + str(arg) + " stations aléatoires"
    random.shuffle(listeData)
    embed = discord.Embed(title=title, color=RED)
    for k in listeData :
        embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
        cpt += 1
        if cpt >= arg: 
            break

    await ctx.send(embed = embed)

@bot.command()
async def all(ctx):
    listeData = updateData()
    cpt = 0
    random.shuffle(listeData)
    embed = discord.Embed(title="Liste des 20 stations aléatoires", color=RED)
    for k in listeData :
        embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
        cpt += 1
        if cpt >= 20: 
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
    response = []
    for k in listeData :
        if arg in k["nom"]:
            response.append(k)
            found = True
    if (len(response) > 5):
        embed = discord.Embed(title="Oops :/", description="Il semblerai que trop de stations correspondent a votre recherche (" + str(len(response)) + ")", color=RED)
        embed.add_field(name="Veuillez préciser votre recherche", value="Exemple : !station Place Carnot à la place de : !station Place", inline=False)
        embed.add_field(name="Maximum autorisé", value="5", inline=False)
        await ctx.send(embed = embed)
    elif not found:
        embed = discord.Embed(title="Oops :/", description="Aucune station ne correspond à votre recherche", color=RED)
        await ctx.send(embed = embed)
    else :
        for k in response:
            embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"], color=RED)        
            embed.add_field(name="*Vélos disponibles*", value=str(k["nbVelo"]), inline=True)
            embed.add_field(name="*Places disponibles*", value=str(k["nbPlace"]), inline=True)
            found = True
            await ctx.send(embed = embed)

# addfav command that add a velov station to the favorite list
@bot.command()
async def add(ctx, arg, arg2=None, arg3=None, arg4=None):
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
            if addToFavorite(k):
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " ajoutée aux favoris", color=GREEN)
            else :
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " déjà dans les favoris", color=BLUE)
            found = True
            break
    if not found:
        embed = discord.Embed(title="Oops :/", description="Aucune station ne correspond à votre recherche", color=RED)

    await ctx.send(embed = embed)

# delfav command that delete a velov station from the favorite list
@bot.command()
async def remove(ctx, arg, arg2=None, arg3=None, arg4=None):
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
            if removeFromFavorite(k):
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " retirée des favoris", color=GREEN)
            else :
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " n'est pas dans les favoris", color=BLUE)
            found = True
            break
    if not found:
        embed = discord.Embed(title="Oops :/", description="Aucune station ne correspond à votre recherche", color=RED)

    await ctx.send(embed = embed)

# fav command that returns the favorite list
@bot.command()
async def fav(ctx):
    if len(favorite) == 0:
        embed = discord.Embed(title="Oops :/", description="Aucune station n'est dans vos favoris", color=BLUE)
    else :
        embed = discord.Embed(title="Liste des stations favorites", color=RED)
        for k in favorite :
            embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
    await ctx.send(embed = embed)

# update command that returns the update time of the data
@bot.command()
async def update(ctx):
    listeData = updateData()

    if (int(time.time()) - clock) < 1:
        text = "Plus de 60 secondes => mise à jour des données"
    else:
        text = str(int(time.time()) - clock) + " secondes (max 60)"

    embed = discord.Embed(title="Mise a jour des données", color=GREEN)
    embed.add_field(name="Temps depuis la dermière maj des données", value=text, inline=False)
    embed.add_field(name="Nombre de stations", value=str(len(listeData)), inline=False)
    embed.add_field(name="Nombre de velovs parkés", value=str(totalVelovs(listeData)), inline=False)
    embed.add_field(name="Nombre de favoris", value=str(len(favorite)), inline=False)
    
    await ctx.send(embed = embed)

# Bot run

bot.run(os.getenv('TOKEN'))