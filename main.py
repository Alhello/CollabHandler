import json
import traceback
import discord
import time
from discord.ext import commands, tasks

TOKEN = "lmao im not giving you the password to my bot"

client = commands.Bot(command_prefix = "!", intents=discord.Intents.all())

with open("collabs.json", "r") as file:
    collabs = json.load(file)
with open("server.json", "r") as file:
    server = json.load(file)

async def handle_exception(ctx, e:Exception):
    await ctx.send("An error has occured. The error is sent to the host, and will be fixed shortly after (hopefully.. im a dummy soo).")
    bot_test = client.get_channel(1368714728578224240)
    await bot_test.send(f"<@1000003118932701234> An error has occured in {ctx.channel}. Traceback down below:")
    await bot_test.send(f"```{traceback.format_exc()}```")

@client.event
async def on_ready():
    print("Bot is up and running!")
    send_scheds.start()
    replacepartprog.start()

@client.event
async def on_thread_create(thread: discord.Thread):
    global server
    if isinstance(thread.parent, discord.ForumChannel):
        judge = client.get_channel(server["judge-channel"])
        for i in thread.applied_tags:
            if i.name == "GP":
                await judge.send(f"<@&{server["gp-judge"]}>")
            elif i.name == "DECO":
                await judge.send(f"<@&{server["deco-judge"]}>")
        link = f"https://discord.com/channels/{thread.guild.id}/{thread.parent.id}/{thread.id}"
        await judge.send(f"New apply post in {link} created by <@{thread.owner_id}>")
        await client.get_channel(1368714728578224240).send("yeh new post")

@client.command()
async def set_server_data(ctx:commands.Context, host, gp_judge, deco_judge, judge_channel):
    global server
    if ctx.author.id != ctx.guild.owner_id:
        return
    server["host"] = int(host)
    server["gp-judge"] = int(gp_judge)
    server["deco-judge"] = int(deco_judge)
    server["judge-channel"] = int(judge_channel)
    open("server.json", "w").write(json.dumps(server))
    await ctx.send("Server data overwritten")


@client.command()
@commands.has_permissions(manage_roles=True)
async def create(ctx:commands.Context, name, perm_gp, perm_deco, gp, deco, song):
    global collabs, server
    if ctx.author.id != server["host"]:
        return
    try:
        await ctx.send(f"Collab {name}, {song}, {perm_gp} | {perm_deco} or above")
        await ctx.send(f"{gp} gameplay parts and {deco} deco parts")
        await ctx.send("Hang on...")
        if name in collabs:
            await ctx.send(f"Collab {name} already exists")
            return
        
        guild = ctx.guild

        role = await guild.create_role(name=name)
        catergory = await guild.create_category(name=f"Collab {name}")

        info = await catergory.create_text_channel(name="info", overwrites=
                                      {
                                          guild.default_role: discord.PermissionOverwrite(
                                              view_channel=True,
                                              send_messages=False,
                                              )
                                        }
                                      )
        finished = await catergory.create_text_channel(name="finished", overwrites=
                                      {
                                          guild.default_role: discord.PermissionOverwrite(
                                              view_channel=True,
                                              send_messages=False,
                                              )
                                        }
                                      )
        progress = await catergory.create_text_channel(name="progress", overwrites=
                                      {
                                          guild.default_role: discord.PermissionOverwrite(view_channel=False),
                                          role: discord.PermissionOverwrite(
                                              view_channel=True,
                                              send_messages=True,
                                              ),
                                        }
                                      )

        collabs[name] = {
            "song": song,
            "permission": [perm_gp, perm_deco],
            "collab-data":
            {
                "catergory": catergory.id,
                "info": info.id,
                "finished": finished.id,
                "progress": progress.id,
                "scheds-time": time.time() + (7*24*3600),
                "role": role.id,
            },
            "parts": 
            {
                "gp": [],
                "deco": [] 
                },
            "quitted": []
            }
        for _ in range(int(gp)): collabs[name]["parts"]["gp"].append({
            "id": "", 
            "start_time": 0,
            "progress": 0,
            })
        for _ in range(int(deco)): collabs[name]["parts"]["deco"].append({
            "id": "", 
            "start_time": 0,
            "progress": 0,
            })
        open("collabs.json", "w").write(json.dumps(collabs))
        await ctx.send(f"Collab {name} created")
    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
@commands.has_permissions(manage_roles=True)
async def delete(ctx:commands.Context, name):
    global collabs, server
    if ctx.author.id != server["host"]:
        return
    try:
        await ctx.send(f"Attempting to delete collab {name}")
        await ctx.send("Hang on...")
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
    
        guild = ctx.guild
        await guild.get_role(collabs[name]["collab-data"]["role"]).delete()
        await guild.get_channel(collabs[name]["collab-data"]["catergory"]).delete()
        await guild.get_channel(collabs[name]["collab-data"]["info"]).delete()
        await guild.get_channel(collabs[name]["collab-data"]["progress"]).delete()
        await guild.get_channel(collabs[name]["collab-data"]["finished"]).delete()
        del collabs[name]
        open("collabs.json", "w").write(json.dumps(collabs))

        await ctx.send("Collab successfully removed")
        
    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
@commands.has_permissions(manage_roles=True)
async def kick(ctx:commands.Context, name, _type, part):
    global collabs, server
    if ctx.author.id != server["host"]:
        return
    try:
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        if _type not in ["gp", "deco"]:
            await ctx.send(f"Type can only be gp or deco")
            return
        if len(collabs[name]["parts"][_type]) == 0:
            await ctx.send(f"There are no {_type} parts in this collab")
            return
        if int(part) > len(collabs[name]["parts"][_type]) or int(part) < 1:
            await ctx.send(f"There are only {len(collabs[name]['parts'][_type])} parts in {name}")
            return

        collabs[name]["parts"][_type][int(part)-1]["id"] = ""
        collabs[name]["parts"][_type][int(part)-1]["start_time"] = 0
        collabs[name]["parts"][_type][int(part)-1]["progress"] = 0
        open("collabs.json", "w").write(json.dumps(collabs))

        await ctx.send(f"Kicked user at {name}, {_type}, {part}")


    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
@commands.has_permissions(manage_roles=True)
async def join(ctx:commands.Context, name, _type, part):
    global collabs
    try:
        await ctx.send(f"Joining {name}, hang on...")
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        if _type not in ["gp", "deco"]:
            await ctx.send(f"Type can only be gp or deco")
            return
        if len(collabs[name]["parts"][_type]) == 0:
            await ctx.send(f"There are no {_type} parts in this collab")
            return
        if int(part) > len(collabs[name]["parts"][_type]) or int(part) < 1:
            await ctx.send(f"There are only {len(collabs[name]['parts'][_type])} parts in {name}")
            return
        if len(ctx.author.roles) == 0:
            await ctx.send(f"You don't have roles")
            return
        if collabs[name]["parts"][_type][int(part)-1]["id"] == ctx.author.id:
            await ctx.send(f"You can't join your own part again")
            return
        appearance = 0
        for i in collabs[name]["parts"][_type]:
            if i["id"] == ctx.author.id:
                appearance += 1
        if appearance >= 2:
            await ctx.send(f"You already joined 2 parts; cannot join more")
            return
        if ctx.author.id in collabs[name]["quitted"]:
            await ctx.send("You already quitted this collab; cannot join again unless host agrees")

        roles = ctx.author.roles[1:]
        
        if _type == "gp":
            allowed_role = collabs[name]["permission"][0]
        elif _type == "deco":
            allowed_role = collabs[name]["permission"][1]
        
        for role in roles:
            if len(role.name.split(" ")) == 3 and role.name.split(" ")[0] == "GP" and _type == "gp":
                if role.id >= int(allowed_role):
                    break
                else:
                    await ctx.send(f"Your tier is lower than the allowed joining tier. Cannot join")
                    return
            elif len(role.name.split(" ")) == 3 and role.name.split(" ")[0] in ["GLOW", "MDRN", "ART", "TECH"] and _type == "deco":
                if role.id >= int(allowed_role):
                    break
                else:
                    await ctx.send(f"Your tier is lower than the allowed joining tier. Cannot join")
                    return
        
        collabs[name]["parts"][_type][int(part)-1]["id"] = ctx.author.id
        collabs[name]["parts"][_type][int(part)-1]["start_time"] = time.time()
        open("collabs.json", "w").write(json.dumps(collabs))
        
        
        guild = ctx.guild
        
        await ctx.author.add_roles(guild.get_role(collabs[name]["collab-data"]["role"]))
        await ctx.send(f"Joined {name}")
                
    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
@commands.has_permissions(manage_roles=True)
async def quit(ctx:commands.Context, name, _type, part):
    global collabs
    try:
        await ctx.send(f"Quitting {name}, hang on...")
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        if _type not in ["gp", "deco"]:
            await ctx.send(f"Type can only be gp or deco")
            return
        if len(collabs[name]["parts"][_type]) == 0:
            await ctx.send(f"There are no {_type} parts in this collab")
            return
        if int(part) > len(collabs[name]["parts"][_type]) or int(part) < 1:
            await ctx.send(f"There are only {len(collabs[name]['parts'][_type])} parts in {name}")
            return
        if collabs[name]["parts"][_type][int(part)-1]["id"] != ctx.author.id:
            await ctx.send(f"You can't quit a part that isn't yours or there is no existing person in the part")
            return
        if collabs[name]["parts"][_type][int(part)-1]["progress"] == "FINISHED":
            await ctx.send(f"Cannot quit part if it is completed")
            return

        collabs[name]["parts"][_type][int(part)-1]["id"] = ""
        collabs[name]["parts"][_type][int(part)-1]["start_time"] = 0
        collabs[name]["parts"][_type][int(part)-1]["progress"] = 0
        open("collabs.json", "w").write(json.dumps(collabs))

        await ctx.send("You have successfully quitted your part")


    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
async def progress(ctx:commands.Context, name, _type, part):
    global collabs, server
    try:
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        if _type not in ["gp", "deco"]:
            await ctx.send(f"Type can only be gp or deco")
            return
        if len(collabs[name]["parts"][_type]) == 0:
            await ctx.send(f"There are no {_type} parts in this collab")
            return
        if int(part) > len(collabs[name]["parts"][_type]) or int(part) < 1:
            await ctx.send(f"There are only {len(collabs[name]['parts'][_type])} parts in {name}")
            return
        if collabs[name]["parts"][_type][int(part)-1]["id"] != ctx.author.id:
            await ctx.send(f"You can't send progress a part that isn't yours or there is no existing person in the part")
            return
        if collabs[name]["parts"][_type][int(part)-1]["progress"] == "FINISHED":
            await ctx.send(f"Cannot send progress for the part if it is completed")
            return
        if not ctx.message.attachments:
            await ctx.send(f"Attach your progress video/photo(s) before sending your progress")
            return
        
        link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}"
        judge = client.get_channel(server["judge-channel"])
        await judge.send(f"A new progress post for collab {name} in {link}, <@&1371252123114672168>")

    except Exception as e:
        await handle_exception(ctx, e)


@client.command()
async def setprog(ctx:commands.Context, name, _type, part, prog):
    global collabs, server
    if ctx.author.id != server["host"]:
        return
    try:
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        if _type not in ["gp", "deco"]:
            await ctx.send(f"Type can only be gp or deco")
            return
        if len(collabs[name]["parts"][_type]) == 0:
            await ctx.send(f"There are no {_type} parts in this collab")
            return
        if int(part) > len(collabs[name]["parts"][_type]) or int(part) < 1:
            await ctx.send(f"There are only {len(collabs[name]["parts"][_type])} parts in {name}")
            return

        collabs[name]["parts"][_type][int(part)-1]["progress"] = prog
        channel_progress = client.get_channel(collabs[name]["collab-data"]["progress"])
        open("collabs.json", "w").write(json.dumps(collabs))
        await channel_progress.send(f"<{collabs[name]['parts'][_type][int(part)-1]['id']}>, your part's progress has been changed to {prog}")

    except Exception as e:
        await handle_exception(ctx, e)

@client.command()
async def getcollabprog(ctx:commands.Context, name):
    global collabs, server
    if ctx.author.id != server["host"]:
        return
    try:
        if name not in collabs:
            await ctx.send(f"Collab {name} doesn't exist")
            return
        await ctx.send(genpartprog(name))
        
    except Exception as e:
        await handle_exception(ctx, e)

@tasks.loop(seconds=30)
async def send_scheds():
    global collabs
    current_time = time.time()
    for i in collabs:
        if current_time >= collabs[i]["collab-data"]["scheds-time"] and abs(current_time - collabs[i]["collab-data"]["scheds-time"]) <= 30:
            channel = client.get_channel(int(collabs[i]["collab-data"]["progress"]))
            if channel:
                try:
                    await channel.send(f"<@{collabs[i]['collab-data']['role']}> send progress")
                except Exception as e:
                    print("Message sent failure.")
            
        if current_time >= collabs[i]["collab-data"]["scheds-time"]:
            while collabs[i]["collab-data"]["scheds-time"] <= current_time:
                collabs[i]["collab-data"]["scheds-time"] += 7*24*3600
            collabs[i]["collab-data"]["scheds-time"] += 7*24*3600
            open("collabs.json", "w").write(json.dumps(collabs))

@tasks.loop(seconds=30)
async def replacepartprog():
    global collabs
    for collab in collabs:
        #info_message = client.get_channel(collabs[collab]["collab-data"]["info"]).last_message if client.get_channel(collabs[collab]["collab-data"]["info"]).last_message else 0
        info_message = [i async for i in client.get_channel(collabs[collab]["collab-data"]["info"]).history(limit=1)][0] if client.get_channel(collabs[collab]["collab-data"]["info"]).history(limit=1) != [] else 0
        #print()
        #print(client.get_channel(collabs[collab]["collab-data"]["info"]).last_message, genpartprog(collab))
        if info_message == 0: return
        if info_message.author.id != client.user.id:
            continue
        await info_message.edit(content=genpartprog(collab))

def genpartprog(name):
    global collabs
    text = ""
    if len(collabs[name]["parts"]["gp"]):
        text += "GP PARTS: \n"
        for i in enumerate(collabs[name]["parts"]["gp"]):
            if not i[1]["id"]:
                text += f"{i[0]+1}: NOT TAKEN\n"
                continue
            text += f"{i[0]+1}: <@{i[1]['id']}>, STARTED AT {i[1]['start_time']}, "
            match i[1]["progress"]:
                case 0:
                    text += "PROGRESS: :red_square:\n"
                case "WORKING":
                    text += "PROGRESS: :yellow_square:\n"
                case "FINISHED":
                    text += "PROGRESS: :green_square:\n"
    if len(collabs[name]["parts"]["deco"]):
        text += "DECO PARTS: \n"
        for i in enumerate(collabs[name]["parts"]["deco"]):
            if not i[1]["id"]:
                text += f"{i[0]+1}: NOT TAKEN\n"
                continue
            text += f"{i[0]+1}: <@{i[1]['id']}>, STARTED AT {i[1]['start_time']}, "
            match i[1]["progress"]:
                case 0:
                    text += "PROGRESS: :red_square:\n"
                case "WORKING":
                    text += "PROGRESS: :yellow_square:\n"
                case "FINISHED":
                    text += "PROGRESS: :green_square:\n"
    return text

@send_scheds.before_loop
async def before_weekly_check():
    await client.wait_until_ready()

client.run(TOKEN)