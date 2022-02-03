#!/usr/bin/env python3

import json
from os.path import exists
import discord
from discord.ext import commands


COURSE_PATH = "./courses.json"
TOKEN_PATH = "./TOKEN"

PRONOUNS = {
    "❤️": "they/them",
    "💛": "he/him",
    "💚": "any pronouns",
    "🧡": "she/her",
    "💙": "just my name",
    "💜": "please ask"
}

bot = commands.Bot(
    command_prefix="!", 
    intents=discord.Intents.all())


def load_course(guild_name):
    with open(COURSE_PATH) as f:
        courses = json.load(f)
        if guild_name not in courses:
            return None
        return courses[guild_name]


def load_roster(course):
    if exists(course["roster_path"]):
        with open(course["roster_path"]) as f:
            return json.load(f)
    else:
        print(f'ERROR: roster file for {course} does not exist')


@bot.event
async def on_ready():
    print("UVAuth is online!")


@bot.event
async def on_member_join(member):
    '''
    dm students for verification
    '''
    print(f"{member} joined {member.guild.name}")
    
    unverified = discord.utils.get(member.guild.roles, name="Unverified")

    await member.add_roles(unverified)
    await member.send(
        f"Hello there! You've joined {member.guild.name}. "
        "Please reply with your computing ID so that you can be verified.")


@bot.event
async def on_message(message):
    '''
    accept student dms for valid computing ids,
    remove unverified role upon correct id
    '''
    await bot.process_commands(message)

    if not isinstance(message.channel, discord.channel.DMChannel):
        return

    user = message.author
    if user == bot.user:
        return

    print(f"received a DM from {user}")

    computing_id = message.content.lower()

    for guild in bot.guilds:        
        course = load_course(guild.name)
        user_member = guild.get_member(user.id)
        if course is None or user_member is None:
            continue

        roster = load_roster(course)
        if roster is None:
            # TODO tell student that roster not implemented
            continue

        if computing_id not in roster:
            print(f"{user} provided an invalid computing id")
            await message.channel.send(
                'Sorry, you either entered an invalid computing id, or you are '
                f'not on the class roster for {guild.name}! Please '
                'try again.')
            await message.channel.send(
                'If your id was correct, you may need to be added to the class '
                f'roster. In that case, please email {course["support_email"]} '
                'to request access.')
            continue

        student = roster[computing_id]

        if "student" not in student["role"].lower():
            print(f"{user} tried to access a non-student role")
            await message.channel.send(
                'You provided the computing id of a staff member involved with '
                f'{guild.name}.  If this is correct, please email '
                f'{course["support_email"]} to be verified manually.  '
                'Otherwise, please try again.')
            continue

        for member in guild.members:
            if member.nick is None: 
                member.nick = member.name
            if computing_id in member.nick.lower():
                print(f'{user} tried to enter the verified id {computing_id}')
                await message.channel.send(
                    'Sorry, the computing id you entered has already been '
                    f'verified to a Discord user in {guild.name}.'
                )
                await message.channel.send(
                    'If you did not previously link this computing id or you '
                    'wish to switch which Discord user is verifed to your id, '
                    f'please email {course["support_email"]} for help.')
        print(
            f'removing Unverified role and adding computing id {computing_id} '
            f'to user {user}')
            
        nickname = f'{student["name"]} ({computing_id})'
        if len(nickname) > 32: 
            nickname = f'{student["name"].split()[0]} ({computing_id})'
        if len(nickname) > 32: 
            nickname = f'{student["name"].split()[0][0]} ({computing_id})'
        
        await user_member.edit(nick=nickname, roles=[])
        await message.channel.send(
            f'Welcome to {guild.name}! You should now have access '
            'to all of the student channels in the course server. If you have '
            'any questions, send a message in "#💬general". Pay attention to '
            '"#📣announcements" for important course announcements.')
        await message.channel.send(
            'If you would like to specify your pronouns, please refer to '
            '"#pronouns "for more.')


@bot.event
async def on_raw_reaction_add(payload):
    '''
    give student pronoun role upon appropriate reaction
    '''
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)

    if channel.name != "pronouns":
        return

    member = guild.get_member(payload.user_id)
    guild_roles = await guild.fetch_roles()
    reaction = str(payload.emoji)

    if reaction in PRONOUNS:
        pronoun_role = discord.utils.get(guild_roles,name=PRONOUNS[reaction])
        await member.add_roles(pronoun_role)
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
    
    if channel.name != "pronouns":
        return
    
    member = guild.get_member(payload.user_id)
    guild_roles = await guild.fetch_roles()
    reaction = str(payload.emoji)

    if reaction in PRONOUNS:
        pronoun_role = discord.utils.get(guild_roles,name=PRONOUNS[reaction])
        await member.remove_roles(pronoun_role)

    print(f"removed the pronoun role associated with {reaction} to {member}")


@bot.command()
@commands.has_role("Admin")
async def say(ctx, arg):
    await ctx.send(arg)


@bot.command()
@commands.has_role("Admin")
async def react(ctx, message_id, *emojis):
    print()
    message = await ctx.channel.fetch_message(message_id)
    for emoji in emojis:
        await message.add_reaction(emoji)


@bot.command()
@commands.has_role("Admin")
async def ping(ctx):
    print(f"{ctx.author} sent a ping!")
    await ctx.send("ping!")


@bot.command()
@commands.has_role("Admin")
async def get_unverified(ctx):
    print(f"{ctx.author} called get_unverified")

    course = load_course(ctx.guild.name)
    if course is None:
        # TODO print that this course not registered in courses
        return

    roster = load_roster(course)
    if roster is None:
        return

    staff = discord.utils.get(ctx.guild.roles, name="Staff")
    unverified = discord.utils.get(ctx.guild.roles, name="Unverified")

    unverified_ids = []
    for comp_id in roster.keys():
        if "student" not in roster[comp_id]["role"].lower(): continue
        
        for member in ctx.guild.members:
            if staff in member.roles or unverified in member.roles: 
                continue
            if member.nick is None: 
                member.nick = member.name
            if comp_id in member.nick:
                unverified_ids.append(comp_id)
                break

    if unverified_ids:
        unverified_ids.sort()
        print(f"here are the unverified students: {unverified_ids}")
        await ctx.send(f"here are the unverified students: {unverified_ids}")
    else:
        print(f"all the students are verified!")
        await ctx.send(f"all the students are verified!")


if __name__ == "__main__":
    # begin event loop using token
    with open(TOKEN_PATH) as file:
        token = file.read()

    bot.run(token)