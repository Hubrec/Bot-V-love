import discord
import os
from discord.ext import commands
import random
from dotenv import load_dotenv
import time

load_dotenv()

# Bot Prefix

description = '''Bot de gestion des stations velovs de Lyon'''

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
    global listeData
    if int(time.time()) - clock >= 60:
        clock = int(time.time())
        listeData = fetchData()
    return listeData

# api localisation requests / data fetching

import requests

# function that returns the user's coordinates or an error message (embed)
def getCoords():
    try:
        ip = requests.get('https://api.ipify.org').text
        url = 'http://ip-api.com/json/'
        geo_req = requests.get(url+ip)
        geo_json = geo_req.json()
        return [geo_json['lat'], geo_json['lon']]
    except:
        embed = discord.Embed(title="Oops :/", description="Impossible de trouver votre position", color=RED)
        return embed

# Favorite storage

favorite = {}
coordsUsers = {}

def addCrds(user, name, crds):
    if user not in coordsUsers:
        coordsUsers[user] = {}
    if name in coordsUsers[user]:
        return False
    coordsUsers[user][name] = crds
    return True

def removeCrds(user):
    if user not in coordsUsers:
        return False
    coordsUsers[user].clear()
    coordsUsers.pop(user)
    return True

def addToFavorite(station, user):
    if user not in favorite:
        favorite[user] = []
    for k in favorite[user]:
        if k["nom"] == station["nom"]:
            return False
    favorite[user].append(station)
    return True

def removeFromFavorite(station, user):
    if user not in favorite:
        return False
    for k in favorite[user]:
        if k["nom"] == station["nom"]:
            favorite[user].remove(k)
            return True
    return False

def updateFavorite():
    for k in listeData:
        for user in favorite:
            for station in favorite[user]:
                if station["nom"] == k["nom"]:
                    station["nbVelo"] = k["nbVelo"]
                    station["nbPlace"] = k["nbPlace"]

# Velovs Data Calculs

def concat(arg, arg2, arg3, arg4):
    if arg2 is not None:
        arg += " " + arg2
        if arg3 is not None:
            arg += " " + arg3
            if arg4 is not None:
                arg += " " + arg4
    return arg

def totalVelovs(data):
    total = 0
    for k in data:
        total += k["nbVelo"]
    return total

def totalPlaces(data):
    total = 0
    for k in data:
        total += k["nbPlace"]
    return total

def getclosestStations(data, lat, lon):
    for k in data:
        k["distance"] = (lat - k["latitude"])**2 + (lon - k["longitude"])**2
    data.sort(key=lambda x: x["distance"])
    return data[:5]

# Bot Startup

# when the bot is ready
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
    embed.add_field(name="!addCoords <STRING> <LAD> <LON>", value="J'ajoute les coordonnées entrées à votre liste de coordonnées", inline=False)
    embed.add_field(name="!removeCoords", value="Je retire toutes vos coordonnées de votre liste de coordonnées", inline=False)
    embed.add_field(name="!coords", value="Je vous envoie la liste de vos coordonnées enregistrées", inline=False)
    embed.add_field(name="!search <LAD> <LON>", value="Renvoi les 5 stations les plus proches des coordonnées entrées, vous pouvez aussi entrer a la place des coordonnées le nom d'une de vos addresses enregistrées ou bien encore écrire \"here\" pour rechercher les stations les plus proches de la ou votre réseau émet", inline=False)
    embed.add_field(name="!update", value="Je vous renvoi un panneau d'informations de l'état du réseau et *refresh* les données (fait automatiquement toutes les 60 secondes)", inline=False)
    await ctx.send(embed = embed)

# all command that returns a list of velov stations
@bot.command()
async def rand(ctx, arg):
    listeData = updateData()
    cpt = 0
    arg = int(arg)
    if arg > 20:
        arg = 20
    title = "Liste des " + str(arg) + " stations aléatoires"
    random.shuffle(listeData)
    embed = discord.Embed(title=title, color=BLUE)
    for k in listeData :
        embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
        cpt += 1
        if cpt >= arg: 
            break
    await ctx.send(embed = embed)

# all command that returns a list of 20 velov stations
@bot.command()
async def all(ctx):
    listeData = updateData()
    cpt = 0
    random.shuffle(listeData)
    embed = discord.Embed(title="Liste des 20 stations aléatoires", color=BLUE)
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
    arg = concat(arg, arg2, arg3, arg4)
    arg = str(arg).upper()
    found = False
    response = []
    for k in listeData :
        if arg in k["nom"]:
            response.append(k)
            found = True
    if len(response) > 5:
        embed = discord.Embed(title="Oops :/", description="Il semblerai que trop de stations correspondent a votre recherche (" + str(len(response)) + ")", color=RED)
        embed.add_field(name="Veuillez préciser votre recherche", value="Exemple : !station Place Carnot à la place de : !station Place", inline=False)
        embed.add_field(name="Maximum autorisé", value="5", inline=False)
        await ctx.send(embed = embed)
    elif not found:
        embed = discord.Embed(title="Oops :/", description="Aucune station ne correspond à votre recherche", color=RED)
        await ctx.send(embed = embed)
    else :
        for k in response:
            embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"], color=BLUE)        
            embed.add_field(name="*Vélos disponibles*", value=str(k["nbVelo"]), inline=True)
            embed.add_field(name="*Places disponibles*", value=str(k["nbPlace"]), inline=True)
            found = True
            await ctx.send(embed = embed)

# add command that add a velov station to the favorite list
@bot.command()
async def add(ctx, arg, arg2=None, arg3=None, arg4=None):
    user = ctx.message.author.id
    listeData = updateData()
    arg = concat(arg, arg2, arg3, arg4)
    arg = str(arg).upper()
    found = False
    response = []
    for k in listeData :
        if arg in k["nom"]:
            response.append(k)
            found = True
    if len(response) > 1 and len(response) <= 5:
        for k in response:
            embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"], color=BLUE)        
            embed.add_field(name="*Vélos disponibles*", value=str(k["nbVelo"]), inline=True)
            embed.add_field(name="*Places disponibles*", value=str(k["nbPlace"]), inline=True)
            await ctx.send(embed = embed)

        embed = discord.Embed(title="Oops :/", description="Attention " + str(len(response)) + " stations correspondent a votre recherche", color=RED)
        embed.add_field(name="Veuillez préciser votre recherche", value="Exemple : !station Place Carnot à la place de : !station Place", inline=False)
        embed.add_field(name="Maximum autorisé", value="1", inline=False)
        await ctx.send(embed = embed)
    elif len(response) > 5:
        embed = discord.Embed(title="Oops :/", description="Il semblerai que trop de stations correspondent a votre recherche (" + str(len(response)) + ")", color=RED)
        embed.add_field(name="Veuillez préciser votre recherche", value="Exemple : !station Place Carnot à la place de : !station Place", inline=False)
        embed.add_field(name="Maximum autorisé", value="1", inline=False)
        await ctx.send(embed = embed)
    else:
        for k in response:
            if addToFavorite(k, user):
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " ajoutée aux favoris", color=GREEN)
            else :
                embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " est déjà dans les favoris", color=RED)
            await ctx.send(embed = embed)
    if not found:
        embed = discord.Embed(title="Oops :/", description="Aucune station ne correspond à votre recherche", color=RED)
        await ctx.send(embed = embed)

# delete command that delete a velov station from the favorite list
@bot.command()
async def remove(ctx, arg, arg2=None, arg3=None, arg4=None):
    user = ctx.message.author.id
    arg = concat(arg, arg2, arg3, arg4)
    arg = str(arg).upper()
    found = False
    if len(favorite) == 0:
        embed = discord.Embed(title="Oops :/", description="Aucune station n'est dans vos favoris", color=RED)
        await ctx.send(embed = embed)
    else:
        for k in favorite :
            if arg in k["nom"]:
                if removeFromFavorite(k, user):
                    embed = discord.Embed(title="Station n°" + str(k["numero"]) + ' - ' + k["nom"] + " retirée des favoris", color=GREEN)
                    found = True
                    await ctx.send(embed = embed)
        if not found:
            embed = discord.Embed(title="Oops :/", description="Aucune station dans vos favoris ne correspond à votre recherche", color=RED)
            await ctx.send(embed = embed)

# fav command that returns the favorite list
@bot.command()
async def fav(ctx):
    updateFavorite()
    user = ctx.message.author.id
    if len(favorite) == 0:
        embed = discord.Embed(title="Oops :/", description="Votre liste de favoris est vide !", color=RED)
        embed.add_field(name="Tip", value="Vous pouvez en ajouter avec la commande !add <nom de la station>", inline=False)
    else :
        embed = discord.Embed(title="Liste des stations favorites", color=BLUE)
        for k in favorite[user] :
            embed.add_field(name="Station n°" + str(k["numero"]) + ' - ' + k["nom"], value="*Vélos disponibles* : " + str(k["nbVelo"]) + "\n" + "*Places disponibles* : " + str(k["nbPlace"]), inline=False)
    await ctx.send(embed = embed)

@bot.command()
async def addCoords(ctx, name, lat, lon):
    user = ctx.message.author.id
    lat = float(lat)
    lon = float(lon)
    if not isinstance(lat, float) or not isinstance(lon, float):
        embed = discord.Embed(title="Oops :/", description="Latitude et longitude doivent être des coordonnées", color=RED)
        await ctx.send(embed = embed)
        return
    crds = [lat, lon]
    if addCrds(user, name, crds):
        embed = discord.Embed(title="Coordonnées ajoutées", color=GREEN)
        await ctx.send(embed = embed)
    else:
        embed = discord.Embed(title="Oops :/", description="Vous avez déjà des coordonnées avec ce nom", color=RED)
        await ctx.send(embed = embed)

@bot.command()
async def removeCoords(ctx):
    user = ctx.message.author.id
    if removeCrds(user):
        embed = discord.Embed(title="Coordonnées supprimées", color=GREEN)
        await ctx.send(embed = embed)
    else:
        embed = discord.Embed(title="Oops :/", description="Vous n'avez pas de coordonnées enregistrées", color=RED)
        await ctx.send(embed = embed)

@bot.command()
async def coords(ctx):
    user = ctx.message.author.id
    if user in coordsUsers:
        embed = discord.Embed(title="Coordonnées enregistrées", color=BLUE)
        for k in coordsUsers[user]:
            embed.add_field(name=k, value="Latitude : " + str(coordsUsers[user][k][0]) + "\nLongitude : " + str(coordsUsers[user][k][1]), inline=False)
    else:
        embed = discord.Embed(title="Oops :/", description="Vous n'avez pas de coordonnées enregistrées", color=RED)
    await ctx.send(embed = embed)

@bot.command()
async def search(ctx, lat=None, lon=None):
    listeData = updateData()
    if str(lat) == "here" or str(lon) == "here":
        location = getCoords()
        if isinstance(location, discord.Embed):
            await ctx.send(embed = location)
            return
        else:
            lat = location[0]
            lon = location[1]
    elif isinstance(lat, str) and lon == None:
        user = ctx.message.author.id
        if user in coordsUsers:
            if lat in coordsUsers[user]:
                name = lat
                lat = coordsUsers[user][name][0]
                lon = coordsUsers[user][name][1]
    embedErr = discord.Embed(title="Oops :/", description="Latitude et longitude doivent être des coordonnées, \"here\" ou encore un nom de coordonnées que vous avez enregistrées", color=RED)
    if lat == None or lon == None:
        embed = embedErr
        await ctx.send(embed = embed)
        return
    lat = float(lat)
    lon = float(lon)
    if not isinstance(lat, float) or not isinstance(lon, float):
        embed = embedErr
        await ctx.send(embed = embed)
        return
    embed = discord.Embed(title="Liste des stations les plus proches", color=BLUE)
    embed.set_footer(text="coordonnées utilisées : " + str(lat) + " - " + str(lon) + " (latitude longitude)")
    for k in getclosestStations(listeData, lat, lon) :
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
    embed.add_field(name="Nombre de places disponibles", value=str(totalPlaces(listeData)), inline=False)
    embed.add_field(name="Nombre de favoris", value=str(len(favorite)), inline=False)
    await ctx.send(embed = embed)

# Bot run

bot.run(os.getenv('TOKEN'))