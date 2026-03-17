import time
import json
import asyncio
import aiohttp
import discord
from discord.ext import commands
import os
import ProjectUtils as pu #hahahha so funny. im 17 doing this shit
import ErrorCodes as ec

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

script_dir = os.path.dirname(__file__)

keyspath = os.path.join(script_dir, "KEYS.json")
with open(keyspath, "r") as f:
    Keys = json.load(f)

Hypixel_API_Key = Keys["Hypixel_API_Key"]
Discord_Bot_Token = Keys["Discord_Bot_Token"]

linkedplayerspath = os.path.join(script_dir, "LinkedPlayers.json")
with open(linkedplayerspath, "r") as f:
    linkedplayers = json.load(f)

linkedplayersUUIDtoID = linkedplayers["LinkedDiscord"] #call .get(uuid) to retrieve the discord id tied to it
linkedplayersIDtoUUID = linkedplayers["InvertedLinkedDiscord"] #call .get(discordid) to retrieve the uuid tied to it
linkedplayersDevAccess = linkedplayers["AdministraionDiscordIDs"] #list of people with dev access
linkedplayersBlacklist = linkedplayers["BlacklistedDiscordIDs"] #if you end up on this you had to have been an actual bitch for me

playerreputationpath = os.path.join(script_dir, "PlayerReputation.json")
with open(playerreputationpath, "r") as f:
    playerreputation = json.load(f)

playerreputationPlayerRep = playerreputation["PlayerReputation"] #data on someone
playerreputationOutgoingReps = playerreputation["PastReps"] #they expire after 30days but will still be known

# call .get(uuid) to retrive
# rep : int
# timestamps : JSON list[int] should still be called into a dict
# ie timestamps = playerreputaion.get("Timestamps")

@bot.command(hidden=True)
async def dev(ctx, devtype:str = None):

    # TLDR of these commands is for manually reviewing accounts and blocking well known people from getting targeted or prevent abuses
    # Data dumps will return a json of the specified username/person whether be discord or minecraft
    # which one depends on if im manually reviewing a persons outgoing reps or their rep data 
    # (ie i will have access to who has repped someone and what type ie positive or negative)
    # at some point in the future this will be voted on once there are enough active users wheter or not who reps someone is tracked
    # maybe it goes the other way and in fairness so i am no the only one with this info, all reps are made public

    discordid = str(ctx.author.id)

    if discordid not in linkedplayersDevAccess:
        await ctx.send("You do not have access to these commands")  #logically should be unbreakable unless you spoof a known dev's id which i dont think is possible (i think...)
        return

    if devtype == None:
        await ctx.send("See !dev help for a list of dev commands")
        return
    
    if devtype.lower() == "help":
        await ctx.send("No commands yet")
        return
    await ctx.send("Unknown dev command")


@bot.command(help="Link your discord to your Minecraft")
async def linkaccount(ctx, username:str = None):

    global linkedplayersUUIDtoID, linkedplayersIDtoUUID

    if username == None:
        await ctx.send("Please enter a username")
        return

    discordid = str(ctx.author.id)

    if discordid in linkedplayersBlacklist:
        await ctx.send("Somehow you have pissed me off enough to get blacklisted and will not be allowed to link an account and therefore will not gain access to !rep+/- player")
        return

    if discordid in linkedplayersIDtoUUID:
        username = await pu.get_username_from_UUID(uuid)
        await ctx.send(f"This discord account is already linked to a {username}")
        return

    uuid = await pu.get_UUID_from_username(username) #this is to still be able to track people who change users (almost was a retard and was gonna store by usernames)
    print(f"{uuid} for account {username}")

    if uuid == ec.no_UUID_attached.get("errorcode"): #errorcode 201. skips 202 as it is very unlikely for 201 to trigger
        await ctx.send("Please enter a valid username")
        return

    if uuid in linkedplayersUUIDtoID: #prevent flooding api with people who are already linked
        linkeddiscord = linkedplayersUUIDtoID.get(uuid)
        await ctx.send(f"{username} is already linked to {linkeddiscord}") #MIGHT REMOVE TO PREVENT STALKING IK PEOPLE WILL BE PISSED IF I SNITCH OUT THE DISCORDID
        return

    linkeddiscord = await pu.get_linked_discord(uuid, Hypixel_API_Key)

    if linkeddiscord == ec.no_player_found.get("errorcode"): #errorcode 102
        await ctx.send(f"{username} hasn't logged into hypixel")
        return

    if linkeddiscord == ec.no_discord_linked.get("errorcode"): #errorcode 202
        await ctx.send(f"{username} has no linked discord (TO BE ADDED TUT LINK)")
        return

    if ctx.author.name != linkeddiscord: #checks the username of who sent the command and if it matches the discord linked to the hypixel player im noting this becuase my variable names are duped here/slightly confusing
        await ctx.send(f"Discord user does not match {username}'s linked discord")
        return

    #eventually change the json write system to pop every 5 mins to save my ssd, even tho i dont expect 1000s of writes a day still good practice

    linkedplayersUUIDtoID[uuid] = str(discordid)
    linkedplayersIDtoUUID[discordid] = str(uuid) 

    writetojsonLinkedPlayers = {
        "LinkedDiscord" : linkedplayersUUIDtoID,
        "InvertedLinkedDiscord" : linkedplayersIDtoUUID
    }

    with open(linkedplayerspath, "w") as f:
        json.dump(writetojsonLinkedPlayers, f, indent=4)

    await ctx.send(f"Successfully linked {username}")
    return

@bot.command(help="Gets the current reputation of someone and past rep changes")
async def currentrep(ctx, username:str = None):

    discordid = str(ctx.author.id)

    if username == None:
        if discordid in linkedplayersIDtoUUID: 
            uuid = linkedplayersIDtoUUID.get(discordid)
            username = await pu.get_username_from_UUID(uuid)
        else:
            await ctx.send("Please enter a username")
            return
    else:
        uuid = await pu.get_UUID_from_username(username)
        print(f"{uuid} for account {username}")

    if uuid == ec.no_UUID_attached.get("errorcode"): #errorcode 201
        await ctx.send("Please enter a valid username")
        return

    realplayer = await pu.check_if_logged_into_hypixel(uuid, Hypixel_API_Key)

    if realplayer == ec.no_player_found.get("errorcode"): #errorcode 102
        await ctx.send(f"{username} is a nick or invalid hypixel player")
        return
    
    if uuid not in playerreputation:
        await ctx.send(f"{username} has no reputation. Feel free to be the first!")
        return
    
    currep = playerreputation.get(uuid).get("Rep")

    await ctx.send(f"{username} has {currep} rep")
    return

@bot.command(help="rep posistively or negatively the player provided")
async def rep(ctx, username:str = None, type:str = None, reason:str = None):

    discordid = str(ctx.author.id)

    if discordid not in linkedplayersIDtoUUID:
        await ctx.send("Please link your minecraft account to rep someone")
        return

    if username == None:
        await ctx.send("Please enter a username")
        return
    
    if type == None:
        await ctx.send("Please state the type: pos or neg")
        return

    uuid = await pu.get_UUID_from_username(username) #this is to still be able to track people who change users (almost was a retard and was gonna store by usernames)
    print(f"{uuid} for account {username}")

    if uuid == ec.no_UUID_attached.get("errorcode"): #errorcode 201. skips 202 as it is very unlikely for 201 to trigger
        await ctx.send("Please enter a valid username")
        return

    if discordid in playerreputationOutgoingReps:
        personspastreps = playerreputationOutgoingReps.get(discordid)
        if uuid in personspastreps:
            reportdata = personspastreps.get(uuid)
            lastreport = reportdata.get("timestamp")
            typeofrep = reportdata.get("repstyle")
            repexpires = lastreport + 604800
            if int(time.time()) < repexpires:
                await ctx.send(f"You already have a outstanding {typeofrep}. Expires <t:{repexpires}:R>")
                return
    else:
        playerreputationOutgoingReps[discordid] = {}
    
    if uuid in playerreputationPlayerRep:  #check database to see if the player has rep, if not create a default data structure for the person
        repdata = playerreputationPlayerRep.get(uuid)
    else:
        repdata = {
            "rep" : 0,
            "WhoHasRepped" : {},
            "SpecialTags" : []
        }

        playerreputationPlayerRep[uuid] = repdata

    personspastreps = playerreputationOutgoingReps.get(discordid)

    if reason == None:
        reason = "No reason provided"

    if type.lower() == "pos":
        repdata["rep"] += 1
        repdata["WhoHasRepped"][discordid] = {
            "timestamp": int(time.time()),
            "repstyle": "positive",
            "reason": str(reason)
        }

        pastrepdata = {
            "timestamp": int(time.time()),
            "repstyle": "positive",
            "reason": str(reason)
        }

        personspastreps[uuid] = pastrepdata

        await ctx.send(f"You increased {username}'s reputation")
    else:
        repdata["rep"] -= 1
        repdata["WhoHasRepped"][discordid] = {
            "timestamp": int(time.time()),
            "repstyle": "negative",
            "reason": str(reason)
        }

        pastrepdata = {
            "timestamp": int(time.time()),
            "repstyle": "negative",
            "reason": str(reason)
        }

        personspastreps[uuid] = pastrepdata

        await ctx.send(f"You decreased {username}'s reputation")

    writetojsonPlayerReputation = {
        "PlayerReputation" : playerreputationPlayerRep,
        "PastReps" : playerreputationOutgoingReps
    }
    
    with open(playerreputationpath, "w") as f:
        json.dump(writetojsonPlayerReputation, f, indent=4)






        








@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    print("Message detected:", message.content)
    await bot.process_commands(message) #this will get removed when made public

bot.run(Discord_Bot_Token)
    






