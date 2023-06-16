
import random
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
from discord.ui import Button ,View
from datetime import datetime
import asyncio

from discord.member import Member

with open("config.json", "r") as f:
    config = eval(f.read())

DEFAULT_PREFIX = config["prefix"]
Token = config["token"]

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=DEFAULT_PREFIX, case_insensitive=True, intents=intents, help_command=None)

embedTheme = discord.Color.green()

@bot.event
async def on_ready():
    print("I am Ready!")
    await bot.tree.sync()
    print("Synced")

GameLoop = None
LoopPing = None

@bot.hybrid_command(name="play", with_app_command=True, description="Start the Free Fall Game")
async def play(ctx):
    participants = []
    players = { }

    gameRound = 0
    for rounds in range(4):
        gameRound+=1
        timeRemain = 20

        botChoice = random.choice(["a1", "a2", "a3", "a4"])
        print(f"Bot Chose: {botChoice}")

        Buttons = []
        for i in range(4):
            Buttons.append(Button(label=f"A{i+1}", custom_id=f"a{i+1}"))

        async def shoot_callback(interaction: discord.Interaction):
            btn_id = interaction.data["custom_id"]

            if gameRound==1:
                if interaction.user.id not in players.keys() and interaction.user.id not in participants:
                    participants.append(interaction.user.id)
                    players[interaction.user.id] = "none"
                                 
            else:
                if interaction.user.id not in participants:
                    await interaction.response.send_message(f"You cannot Join in the Middle of the Game!", ephemeral=True)
                elif interaction.user.id not in players.keys() and interaction.user.id in participants:
                    await interaction.response.send_message("You Already Lose this Game!", ephemeral=True)
                
            if interaction.user.id in players.keys():
                if players[interaction.user.id] == "none":
                    await interaction.response.send_message(f"{interaction.user.name} Chose {btn_id}", ephemeral=True)
                    players[interaction.user.id] = btn_id
                else:
                    await interaction.response.send_message(f"You have already chose one of them!", ephemeral=True)

            print(participants)
            print(players)
            

        # you can make 2 buttons for lock/unlock channel and if u want to send embeds or send messages from buttons just type : interaction.response.send_message(the message with "")
    
        view = View()

        for btn in Buttons:
            btn.callback = shoot_callback
            view.add_item(btn)

        file = discord.File("images/Main.png", filename="Main.png")
        gameEmbed = discord.Embed(title=f"Free Fall - Round {gameRound} Begins", description=f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `{timeRemain}` Seconds", color=discord.Color.green())
        gameEmbed.set_image(url="attachment://Main.png")
        gamemsg = await ctx.send(embed=gameEmbed, file=file, view=view)
        for k in range(20):
            await asyncio.sleep(1)
            timeRemain-=1
            gameEmbed.description = f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `{timeRemain}` Seconds"
            await gamemsg.edit(embed=gameEmbed)
        else:
            gameEmbed.description = f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `Over`"
            await gamemsg.edit(embed=gameEmbed)
        
        roundLosers = []
        currentPlayers = len(players.keys())
        for plays in list(players.keys()):
            print(list(players.keys()))
            if players[plays] == botChoice or players[plays] == "none":
                
                roundLosers.append(bot.get_user(plays).name)
                del players[plays]
                print("One Player Out!")
            else:
                players[plays] = "none"

        if len(roundLosers) != 0:
            roundLosers = ", ".join(roundLosers)
        else:
            roundLosers = "No One"
        roundEmbed = discord.Embed(title=f"Free Fall - Round {gameRound} Over", description=f"Players Left: `{len(players.keys())}`\n", color=discord.Color.red())
        file = discord.File(f"images/{botChoice.upper()}.png", filename=f"{botChoice.upper()}.png")
        roundEmbed.set_image(url=f"attachment://{botChoice.upper()}.png")
        roundEmbed.set_footer(text=f"The Dangerous Door was the {botChoice.upper()} Door")
        await ctx.send(embed=roundEmbed, file=file)
        await ctx.send(embed=discord.Embed(title=f"Round {gameRound} Losers", description=f"{roundLosers}", color=discord.Color.red()))
        if len(list(players.keys())) == 0:
            await ctx.send("No more Players Left!")
            return
        elif len(list(players.keys())) == 1:
            await ctx.send(f"{bot.get_user(list(players.keys())[0]).name} is the Only Winner!")
            return
        else:
            await asyncio.sleep(2)

        # await ctx.send("```Round Losers: '\n'.join()```")
    gameWinners = []
    for plays in players.keys():
        gameWinners.append(bot.get_user(plays).name)
    players = "\n".join(gameWinners)
    await ctx.send(embed=discord.Embed(title=f"Game Winners", description=f"{players}", color=embedTheme))

@bot.hybrid_command(name="role", with_app_command=True, description="Set a Role to be Pinged in Every Game Loop Turn")
async def role(ctx, anyrole: discord.Role = None):

    global LoopPing
    if anyrole is None:
        await ctx.reply(embed=discord.Embed(description="Usage: `role <role>`", color=embedTheme), ephemeral=True)
        return
    
    LoopPing = anyrole
    await ctx.reply(embed=discord.Embed(description=f"Changed Game Loop Ping Role to {LoopPing.mention}", color=embedTheme))


@bot.hybrid_command(name="help", with_app_command=True, description="Get help!")
async def help(ctx):
    helpEmbed = discord.Embed(title="Commands List", color=embedTheme)
    helpEmbed.description = "\n - Type `/play` to start a 4 rounds Free Fall Game\n- Use `/setgame <duration:hours> <rounds>` to set a Free Fall game loop\n- Use `/setgame stop` to stop Free Fall game loops\n- Use `/role <id/mention>` to get Role Pings when a new loop game starts"
    helpEmbed.set_footer(icon_url=ctx.author.display_avatar.url, text=f"Requested by {ctx.author.name}")

    await ctx.reply(embed=helpEmbed)

gameno = {}

@bot.hybrid_command(name="setgame", with_app_command=True, description="Set a Game to Automatically Start at a Certain Time")
@has_permissions(administrator=True)
async def setgame(ctx, duration=None , rounds=None):
    global GameLoop
    global LoopPing
    if duration is None:
        await ctx.reply(embed=discord.Embed(title="Invalid Duration", color=embedTheme, description="Please Specify Time Duration of the Game!"), ephemeral=True)
        return
    elif duration in ["stop","none","no"]:
        GameLoop = None
        await ctx.reply(embed=discord.Embed(color=embedTheme, description="No Game Loop Running Now!"))
        return
    
    elif rounds is None:
        await ctx.reply(embed=discord.Embed(title="Invalid rounds", color=embedTheme, description="Please Specify Number of Rounds of the Game!"), ephemeral=True)
        return

    try:
        r = int(duration)
    except Exception as e:
        await ctx.reply(embed=discord.Embed(color=embedTheme, description="Wrong Time Format! Duration Must be in Hours Format."), ephemeral=True)
        return
    global gameno
    timeperiod = int(duration) * 60 * 60
    timeinhours = duration
    duration = timeperiod
    gameloop_code = random.randint(000000, 999999)
    if gameloop_code == GameLoop:
        gameloop_code = random.randint(000000, 999999)
        
    GameLoop = gameloop_code
    gameno[gameloop_code] = 0

    totalrounds = int(rounds)

    @tasks.loop(seconds=duration)
    async def gameloop():
        global gameno
        gameno[GameLoop]+=1
        if LoopPing is not None and GameLoop == gameloop_code and gameno[GameLoop]>1:
            allowed_mentions = discord.AllowedMentions(roles = True)
            await ctx.send(f"A New Free Fall Match is Starting! {LoopPing.mention}", allowed_mentions=allowed_mentions)

        if GameLoop == gameloop_code:
            participants = []
            players = { }

            gameRound = 0
            for rounds in range(totalrounds):
                gameRound+=1
                timeRemain = 20

                botChoice = random.choice(["a1", "a2", "a3", "a4"])
                print(f"Bot Chose: {botChoice}")

                Buttons = []
                for i in range(4):
                    Buttons.append(Button(label=f"A{i+1}", custom_id=f"a{i+1}"))

                async def shoot_callback(interaction: discord.Interaction):
                    btn_id = interaction.data["custom_id"]

                    if gameRound==1:
                        if interaction.user.id not in players.keys() and interaction.user.id not in participants:
                            participants.append(interaction.user.id)
                            players[interaction.user.id] = "none"
                                        
                    else:
                        if interaction.user.id not in participants:
                            await interaction.response.send_message(f"You cannot Join in the Middle of the Game!", ephemeral=True)
                        elif interaction.user.id not in players.keys() and interaction.user.id in participants:
                            await interaction.response.send_message("You Already Lose this Game!", ephemeral=True)
                        
                    if interaction.user.id in players.keys():
                        if players[interaction.user.id] == "none":
                            await interaction.response.send_message(f"{interaction.user.name} Chose {btn_id}", ephemeral=True)
                            players[interaction.user.id] = btn_id
                        else:
                            await interaction.response.send_message(f"You have already chose one of them!", ephemeral=True)

                    print(participants)
                    print(players)
                    

                # you can make 2 buttons for lock/unlock channel and if u want to send embeds or send messages from buttons just type : interaction.response.send_message(the message with "")
            
                view = View()

                for btn in Buttons:
                    btn.callback = shoot_callback
                    view.add_item(btn)

                file = discord.File("images/Main.png", filename="Main.png")
                gameEmbed = discord.Embed(title=f"Free Fall - Round {gameRound} Begins", description=f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `{timeRemain}` Seconds", color=discord.Color.green())
                gameEmbed.set_image(url="attachment://Main.png")
                gamemsg = await ctx.send(embed=gameEmbed, file=file, view=view)
                for k in range(20):
                    await asyncio.sleep(1)
                    timeRemain-=1
                    gameEmbed.description = f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `{timeRemain}` Seconds"
                    await gamemsg.edit(embed=gameEmbed)
                else:
                    gameEmbed.description = f"Round {gameRound} \n Players: `{len(list(players.keys()))}`\n Time Remaining: `Over`"
                    await gamemsg.edit(embed=gameEmbed)
                
                roundLosers = []
                currentPlayers = len(players.keys())
                for plays in list(players.keys()):
                    print(list(players.keys()))
                    if players[plays] == botChoice or players[plays] == "none":
                        
                        roundLosers.append(bot.get_user(plays).name)
                        del players[plays]
                        print("One Player Out!")
                    else:
                        players[plays] = "none"

                if len(roundLosers) != 0:
                    roundLosers = ", ".join(roundLosers)
                else:
                    roundLosers = "No One"
                roundEmbed = discord.Embed(title=f"Free Fall - Round {gameRound} Over", description=f"Players Left: `{len(players.keys())}`\n", color=discord.Color.red())
                file = discord.File(f"images/{botChoice.upper()}.png", filename=f"{botChoice.upper()}.png")
                roundEmbed.set_image(url=f"attachment://{botChoice.upper()}.png")
                roundEmbed.set_footer(text=f"The Dangerous Door was the {botChoice.upper()} Door")
                await ctx.send(embed=roundEmbed, file=file)
                await ctx.send(embed=discord.Embed(title=f"Round {gameRound} Losers", description=f"{roundLosers}", color=discord.Color.red()))
                if len(list(players.keys())) == 0:
                    await ctx.send("No more Players Left!")
                    await ctx.send(embed=discord.Embed(description=f"Next Game will Start in {timeinhours} Hours!", color=embedTheme))
                    return
                elif len(list(players.keys())) == 1:
                    await ctx.send(f"{bot.get_user(list(players.keys())[0]).name} is the Only Winner!")
                    await ctx.send(embed=discord.Embed(description=f"Next Game will Start in {timeinhours} Hours!", color=embedTheme))
                    return
                else:
                    await asyncio.sleep(2)

            if len(list(players.keys())) > 1:
                # await ctx.send("```Round Losers: '\n'.join()```")
                gameWinners = []
                for plays in players.keys():
                    gameWinners.append(bot.get_user(plays).name)
                players = "\n".join(gameWinners)
                await ctx.send(embed=discord.Embed(title=f"Game Winners", description=f"{players}", color=embedTheme))
                await ctx.send(embed=discord.Embed(description=f"Next Game will Start in {timeinhours} Hours!", color=embedTheme))
        else:
            return

    print(duration)
    # await asyncio.sleep(duration)

    await gameloop.start()


bot.run(Token)