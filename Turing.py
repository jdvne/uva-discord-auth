'''
TODO:   
        bot commands not working as intended
'''

import json, discord
from discord.ext import commands

class Course:
    def __init__(self, name, guild_id, roster_path):
        self.name = name,
        self.guild_id = guild_id
        self.roster_path = roster_path

TOKEN = "ODAzMjU2NzIwNTQ5MzQ3MzU5.YA7JHQ.SVdy-sCFWZ350xupfYxDbNLsjPg"
GUILD_ID = 877924693196308521
ROSTER_PATH = "./cs3102roster.json"
COHORT_PATH = "./cohorts.csv"

bot = commands.Bot(command_prefix="t!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Turing is online!")

@bot.event
async def on_member_join(member):
    '''
    dm students for verification
    '''
    print(f"{member} joined {member.guild.name}")
    
    unverified = discord.utils.get(member.guild.roles, name="Unverified")

    await member.add_roles(unverified)
    await member.send(f"Hello there! You've joined {member.guild.name}. Please reply with your computing ID so that you can be verified.")

@bot.event
async def on_message(message):
    '''
    accept student dms for valid computing ids,
    remove unverified role upon correct id
    '''
    user = message.author
    if not isinstance(message.channel, discord.channel.DMChannel) or user == bot.user:
        return

    print(f"received a DM from {user}")
    comp_id = message.content.lower()

    for member in bot.get_guild(GUILD_ID).members:
        if member != user: continue

        with open(ROSTER_PATH) as f:
            students = json.load(f)

        if comp_id not in students.keys():
            print(f"{user} provided an invalid computing id")
            await message.channel.send('Sorry, you either entered an invalid computing id, or you are currently not on the class roster! Please try again.')
            # TODO: change this email
            await message.channel.send('If your id was correct, you may need to be added to the class roster. In that case, please email njb2b@virginia.edu to request access.')
            continue

        student = students[comp_id]

        if "student" not in student["role"].lower():
            print(f"{user} tried to access a non-Student role")
            # TODO: change this email
            await message.channel.send("Sorry, you provided the computing id of a staff member involved with the course.  If this is correct, please email njb2b@virginia.edu to be verified manually.")
            continue

        print(f"removing Unverified role and adding computing id {student['id']} to user {user}")
        nickname = student["name"] + ' (' + student["id"] + ')'
        if len(nickname) > 32: nickname = student["name"].split()[0] + ' (' + student["id"] + ')'
        if len(nickname) > 32: nickname = student["name"].split()[0][0] + '. (' + student["id"] + ')'
        await member.edit(nick=nickname, roles=[])
        await message.channel.send('Welcome to the class! You should now have access to all of the student channels in the course server. If you have any questions, send a message in "#💬general". Pay attention to "#📣announcements" for important course announcements.')
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
        
        print(f"gave the pronoun role associated with {reaction} to {member}")

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

        print(f"removed the pronoun role associated with {reaction} to {member}")

@bot.command()
async def ping(ctx):
    print(f"{ctx.author} sent a ping!")
    await ctx.send("ping!")

@bot.command()
async def get_unverified(ctx):
    print(f"{ctx.author} called get_unverified")

    with open(ROSTER_PATH) as f:
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
        print(f"here are the unverified students: {unverified_ids}")
        await ctx.send(f"here are the unverified students: {unverified_ids}")
    else:
        print(f"all the students are verified!")
        await ctx.send(f"all the students are verified!")

bot.run(TOKEN)