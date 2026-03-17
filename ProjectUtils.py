import aiohttp
import asyncio
import json
import ErrorCodes as ec

DEBUG = True

# eventually will tidey up api calls to make it the bare minimum for even uuid and username calls
# for right now i think it double calls only mojang

def debug(ErrorCodeStr):
    if DEBUG:
        print(ErrorCodeStr)

async def get_UUID_from_username(username:str):
    """
    If not used in a discord command put inside a asyncio.run()

    Returns the UUID of a username if avaliable

    Returns None if no UUID is found
    """
    requestLink = "https://api.mojang.com/users/profiles/minecraft/" + username

    async with aiohttp.ClientSession() as session:

        async with session.get(requestLink) as response:

            if response.status == 204: #No username provided
                debug(ec.no_username_provided) #almost never happens so ingore
                return 101
            
            data = await response.json()
            uuid = data.get("id")

            if uuid == None: #No UUID attached to Username
                debug(ec.no_UUID_attached)
                return 201
            
            return uuid

async def get_username_from_UUID(uuid:str):
    """
    If not used in a discord command put inside a asyncio.run()

    Returns the username of a UUID if avaliable

    Returns None if no username is found
    """
    clean_uuid = uuid.replace("-", "")
    requestLink = "https://sessionserver.mojang.com/session/minecraft/profile/" + uuid

    async with aiohttp.ClientSession() as session:

        async with session.get(requestLink) as response:

            if response.status == 204: #No UUID provided
                debug(ec.no_UUID_provided) #almost never happens so ingore
                return 103
            
            data = await response.json()
            name = data.get("name")

            if name == None: #No username attached to UUID
                debug(ec.no_username_attached)
                return 203
            
            return name
        
async def check_if_logged_into_hypixel(uuid:str, apiKey:str):
    """
    If not used in a discord command put inside a asyncio.run()
    
    Returns if a player is nicked or not (if the user is a nicked player the user has not logged into hypixel)
    """

        # IF YOU ARE FROM HYPIXEL REVIEWING MY CODE FOR ACCESS TO A PERSONAL API KEY AND MAYBE IN THE FUTURE A PRODUCTION KEY
        # THIS IS NOT FOR THE PURPOSE OF DENICKING IT IS TO PREVENT WRITING REPUTATION DATA OF A USERNAME/UUID OF A NICK
        # IE PREVENTING DUMMIE DATA FROM GETTING TRACKED
        # THE ONLY ADDITION TO THIS WHICH WILL HAVE TO GET REVIEWED WHEN I GET TO IT IS TRACKING PAST NICKS INTO A CACHE TO REDUCE API LOAD

    if uuid == None:
        return None
    
    requestLink = f"https://api.hypixel.net/player?key={apiKey}&uuid={uuid}"

    async with aiohttp.ClientSession() as session:

        async with session.get(requestLink) as response:

            data = await response.json()

            if data.get("success") == False:
                debug(ec.invalid_hypixel_api_key)
                return 99

            if not data.get("player"):
                debug(ec.no_player_found)
                return 102
            
            return True

async def get_linked_discord(uuid:str, apiKey:str):
    """
    If not used in a discord command put inside a asyncio.run()

    Returns the discord account linked to a minecraft username
    """

    if uuid == None:
        return None
    
    requestLink = f"https://api.hypixel.net/player?key={apiKey}&uuid={uuid}"

    async with aiohttp.ClientSession() as session:

        async with session.get(requestLink) as response:

            data = await response.json()

            if data.get("success") == False:
                debug(ec.invalid_hypixel_api_key)
                return 99

            if not data.get("player"):
                debug(ec.no_player_found)
                return 102

            linkeddiscord = data.get("player").get("socialMedia").get("links").get("DISCORD")

            if linkeddiscord == None: #No UUID attached to Username
                debug(ec.no_discord_linked)
                return 202
            
            return linkeddiscord
        
        
