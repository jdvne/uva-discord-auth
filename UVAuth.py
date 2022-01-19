'''
TODO:   
        implement file logging
'''

import json
from datetime import datetime

import discord
from discord.ext import commands

CONFIG_PATH = "./config.json"
TOKEN_PATH = "./TOKEN"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def get_from_config(attr):
    with open(CONFIG_PATH) as f:
        return json.load(f)[attr]

def log(message):
    if get_from_config("logging")["console"]:
        print(f'[{datetime.now()}] {message}')
    
    if get_from_config("logging")['file']:
        #TODO implement
        pass

def main():
    # begin event loop using token
    with open(TOKEN_PATH) as TOKEN:
        bot.run(TOKEN.read())

@bot.event
async def on_ready():
    log("UVAuth is online!")

@bot.event
async def on_member_join(member):
    '''
    dm students for verification
    '''
    log(f"{member} joined {member.guild.name}")
    
    unverified = discord.utils.get(member.guild.roles, name="Unverified")

    await member.add_roles(unverified)
    await member.send(f"Hello there! You've joined {member.guild.name}. Please reply with your computing ID so that you can be verified.")

@bot.event
async def on_message(message):
    '''
    accept student dms for valid computing ids,
    remove unverified role upon correct id
    '''
    await bot.process_commands(message)

    user = message.author
    if not isinstance(message.channel, discord.channel.DMChannel) or user == bot.user:
        return

    log(f"received a DM from {user}")
    computing_id = message.content.lower()

    for course in get_from_config("courses"):
        for guild in bot.guilds:
            if guild.name == course["server_title"]:
                break

        for member in guild.members:
            if member != user: continue

            with open(course["roster_path"]) as f:
                students = json.load(f)

            if computing_id not in students.keys():
                log(f"{user} provided an invalid computing id")
                await message.channel.send('Sorry, you either entered an invalid computing id, or you are currently not on the class roster! Please try again.')
                await message.channel.send(f'If your id was correct, you may need to be added to the class roster. In that case, please email {course["support_email"]} to request access.')
                continue

            student = students[computing_id]

            if "student" not in student["role"].lower():
                log(f"{user} tried to access a non-Student role")
                await message.channel.send(f"You provided the computing id of a staff member involved with {course['server_title']}.  If this is correct, please email {course['support_email']} to be verified manually.  Otherwise, please try again.")
                continue

            log(f"removing Unverified role and adding computing id {student['id']} to user {user}")
            
            nickname = student["name"] + ' (' + student["id"] + ')'
            if len(nickname) > 32: nickname = student["name"].split()[0] + ' (' + student["id"] + ')'
            if len(nickname) > 32: nickname = student["name"].split()[0][0] + '. (' + student["id"] + ')'
            
            await member.edit(nick=nickname, roles=[])
            await message.channel.send(f'Welcome to {course["server_title"]}! You should now have access to all of the student channels in the course server. If you have any questions, send a message in "#💬general". Pay attention to "#📣announcements" for important course announcements.')
            await message.channel.send('If you would like to specify your pronouns, please refer to #pronouns for more.')
            continue

@bot.event
async def on_raw_reaction_add(payload):
    '''
    give student pronoun role upon appropriate reaction
    '''
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)

    if channel.name == "pronouns":
        member = guild.get_member(payload.user_id)
        guild_roles = await guild.fetch_roles()
        reaction = str(payload.emoji)

        if reaction == "❤️":   await member.add_roles(discord.utils.get(guild_roles,name="they/them"))
        elif reaction == "🧡": await member.add_roles(discord.utils.get(guild_roles,name="she/her"))
        elif reaction == "💛": await member.add_roles(discord.utils.get(guild_roles,name="he/him"))
        elif reaction == "💚": await member.add_roles(discord.utils.get(guild_roles,name="any pronouns"))
        elif reaction == "💙": await member.add_roles(discord.utils.get(guild_roles,name="just my name"))
        elif reaction == "💜": await member.add_roles(discord.utils.get(guild_roles,name="please ask"))
        
        else:
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
            return
        
        log(f"gave the pronoun role associated with {reaction} to {member}")

@bot.event
async def on_raw_reaction_remove(payload):
    '''
    remove student pronoun role upon appropriate reaction removal
    '''
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    if channel.name == "pronouns":
        member = guild.get_member(payload.user_id)
        guild_roles = await guild.fetch_roles()
        reaction = str(payload.emoji)

        if reaction == "❤️":   await member.remove_roles(discord.utils.get(guild_roles,name="they/them"))
        elif reaction == "🧡": await member.remove_roles(discord.utils.get(guild_roles,name="she/her"))
        elif reaction == "💛": await member.remove_roles(discord.utils.get(guild_roles,name="he/him"))
        elif reaction == "💚": await member.remove_roles(discord.utils.get(guild_roles,name="any pronouns"))
        elif reaction == "💙": await member.remove_roles(discord.utils.get(guild_roles,name="just my name"))
        elif reaction == "💜": await member.remove_roles(discord.utils.get(guild_roles,name="please ask"))

        log(f"removed the pronoun role associated with {reaction} to {member}")

@bot.command()
@commands.has_role("Admin")
async def say(ctx, arg):
    await ctx.send(arg)

@bot.command()
@commands.has_role("Admin")
async def react(ctx, message_id, *emojis):
    message = await ctx.channel.fetch_message(message_id)
    for emoji in emojis:
        await message.add_reaction(emoji)

@bot.command()
@commands.has_role("Admin")
async def ping(ctx):
    log(f"{ctx.author} sent a ping!")
    await ctx.send("ping!")

@bot.command()
@commands.has_any_role("Admin", "Professor", "Staff")
async def get_unverified(ctx):
    log(f"{ctx.author} called get_unverified")

    for course in get_from_config("courses"):
        if course["server_title"] == ctx.guild.name:
            with open(course["roster_path"]) as f:
                students = json.load(f)

    staff = discord.utils.get(ctx.guild.roles, name="Staff")
    unverified = discord.utils.get(ctx.guild.roles, name="Unverified")
    unverified_ids = []

    for comp_id in students.keys():
        found = False
        if "student" not in students[comp_id]["role"].lower(): continue
        
        for member in ctx.guild.members:
            if staff in member.roles or unverified in member.roles: continue
            if not member.nick: member.nick = member.name
            if comp_id in member.nick: found = True

        if not found: unverified_ids.append(comp_id)

    if unverified_ids:
        unverified_ids.sort()
        log(f"here are the unverified students: {unverified_ids}")
        await ctx.send(f"here are the unverified students: {unverified_ids}")
    else:
        log(f"all the students are verified!")
        await ctx.send(f"all the students are verified!")

if __name__ == "__main__":
    main()