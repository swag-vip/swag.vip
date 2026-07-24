import discord
from discord.ext import commands
import json
import os
import aiosqlite
import asyncio
from datetime import datetime

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

config = load_config()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config
bot.start_time = datetime.utcnow()

async def init_db():
    bot.db = await aiosqlite.connect("bot_data.db")
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS level_data (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS config (
            guild_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            channel_id INTEGER,
            guild_id INTEGER,
            prize TEXT,
            winner_count INTEGER,
            host_id INTEGER,
            end_time TIMESTAMP,
            ended INTEGER DEFAULT 0
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            guild_id INTEGER,
            user_id INTEGER,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS reaction_roles (
            message_id INTEGER,
            channel_id INTEGER,
            guild_id INTEGER,
            role_id INTEGER,
            emoji TEXT,
            PRIMARY KEY (message_id, role_id)
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS xp_rewards (
            guild_id INTEGER,
            level INTEGER,
            role_id INTEGER,
            PRIMARY KEY (guild_id, level)
        )
    """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS auto_responses (
            guild_id INTEGER,
            trigger TEXT,
            response TEXT,
            PRIMARY KEY (guild_id, trigger)
        )
    """)
    await bot.db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f"Connecté en tant que {bot.user}")
    print(f"Serveurs : {len(bot.guilds)}")
    print(f"Utilisateurs : {sum(g.member_count for g in bot.guilds)}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{len(bot.guilds)} serveurs | /help"
    ))

@bot.command(name="reload")
@commands.is_owner()
async def reload_all(ctx):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.reload_extension(f"cogs.{filename[:-3]}")
                await ctx.send(f"✅ Rechargé `{filename}`")
            except Exception as e:
                await ctx.send(f"❌ Erreur `{filename}`: {e}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"  ✅ {filename}")
            except Exception as e:
                print(f"  ❌ {filename}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(config["token"])

if __name__ == "__main__":
    asyncio.run(main())
