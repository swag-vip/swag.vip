import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_level(self, xp):
        level = 0
        while xp >= (level + 1) * 100:
            level += 1
            xp -= level * 100
        return level

    def xp_for_next_level(self, current_level):
        xp = 0
        for i in range(1, current_level + 2):
            xp += i * 100
        return xp

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        cursor = await self.bot.db.execute(
            "SELECT xp, level FROM level_data WHERE user_id = ? AND guild_id = ?",
            (message.author.id, message.guild.id)
        )
        row = await cursor.fetchone()
        xp_gain = random.randint(15, 30)
        if row:
            new_xp = row[0] + xp_gain
            new_level = self.calculate_level(new_xp)
            if new_level > row[1]:
                await self.bot.db.execute(
                    "UPDATE level_data SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?",
                    (new_xp, new_level, message.author.id, message.guild.id)
                )
                embed = discord.Embed(
                    title="🎉 Niveau supérieur!",
                    description=f"{message.author.mention} est maintenant au **niveau {new_level}**!",
                    color=0xFEE75C
                )
                await message.channel.send(embed=embed)
                cursor2 = await self.bot.db.execute(
                    "SELECT role_id FROM xp_rewards WHERE guild_id = ? AND level = ?",
                    (message.guild.id, new_level)
                )
                reward = await cursor2.fetchone()
                if reward:
                    role = message.guild.get_role(reward[0])
                    if role:
                        try:
                            await message.author.add_roles(role)
                            await message.channel.send(f"🏆 {message.author.mention} a reçu le rôle **{role.name}**!")
                        except:
                            pass
            else:
                await self.bot.db.execute(
                    "UPDATE level_data SET xp = ? WHERE user_id = ? AND guild_id = ?",
                    (new_xp, message.author.id, message.guild.id)
                )
        else:
            await self.bot.db.execute(
                "INSERT INTO level_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                (message.author.id, message.guild.id, xp_gain, 0)
            )
        await self.bot.db.commit()

    @app_commands.command(name="rank", description="Voir le niveau et XP d'un membre")
    @app_commands.describe(membre="Le membre")
    async def rank(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        cursor = await self.bot.db.execute(
            "SELECT xp, level FROM level_data WHERE user_id = ? AND guild_id = ?",
            (membre.id, interaction.guild.id)
        )
        row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message(f"ℹ️ {membre.mention} n'a pas encore de données de niveau.", ephemeral=True)
        xp, level = row
        xp_needed = self.xp_for_next_level(level)
        xp_in_level = xp
        for i in range(1, level + 1):
            xp_in_level -= i * 100
        progress = int((xp_in_level / ((level + 1) * 100)) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        embed = discord.Embed(title=f"📊 Rank de {membre.name}", color=membre.color)
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="Niveau", value=str(level), inline=True)
        embed.add_field(name="XP Total", value=str(xp), inline=True)
        embed.add_field(name="XP Prochain", value=f"{xp_in_level}/{(level + 1) * 100}", inline=True)
        embed.add_field(name="Progression", value=f"`{bar}` {int((xp_in_level / ((level + 1) * 100)) * 100)}%", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Classement XP du serveur")
    async def leaderboard(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT user_id, xp, level FROM level_data WHERE guild_id = ? ORDER BY xp DESC LIMIT 15",
            (interaction.guild.id,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return await interaction.response.send_message("❌ Aucune donnée de niveau.", ephemeral=True)
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (user_id, xp, level) in enumerate(rows):
            user = interaction.guild.get_member(user_id)
            name = user.display_name if user else "Inconnu"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} {name} — Niveau **{level}** | **{xp}** XP\n"
        embed = discord.Embed(title="🏆 Classement XP", description=desc, color=0xFEE75C)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setxp", description="Définir l'XP d'un membre (admin)")
    @app_commands.describe(membre="Le membre", xp="Nouvel XP")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setxp(self, interaction: discord.Interaction, membre: discord.Member, xp: int):
        level = self.calculate_level(xp)
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO level_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
            (membre.id, interaction.guild.id, xp, level)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ XP de {membre.mention} mis à jour: **{xp}** (niveau {level})")

    @app_commands.command(name="resetxp", description="Réinitialiser l'XP d'un membre")
    @app_commands.describe(membre="Le membre")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def resetxp(self, interaction: discord.Interaction, membre: discord.Member):
        await self.bot.db.execute(
            "DELETE FROM level_data WHERE user_id = ? AND guild_id = ?",
            (membre.id, interaction.guild.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ XP de {membre.mention} réinitialisé.")

    @app_commands.command(name="xpreward", description="Définir un rôle récompense pour un niveau")
    @app_commands.describe(level="Niveau requis", role="Le rôle à donner")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def xpreward(self, interaction: discord.Interaction, level: int, role: discord.Role):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO xp_rewards (guild_id, level, role_id) VALUES (?, ?, ?)",
            (interaction.guild.id, level, role.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Le rôle **{role.name}** sera donné au niveau **{level}**.")

    @app_commands.command(name="xprewards", description="Voir les récompenses XP configurées")
    async def xprewards_list(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT level, role_id FROM xp_rewards WHERE guild_id = ? ORDER BY level",
            (interaction.guild.id,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return await interaction.response.send_message("❌ Aucune récompense XP configurée.", ephemeral=True)
        desc = ""
        for level, role_id in rows:
            role = interaction.guild.get_role(role_id)
            role_name = role.mention if role else "Rôle supprimé"
            desc += f"📊 Niveau **{level}** → {role_name}\n"
        embed = discord.Embed(title="🏆 Récompenses XP", description=desc, color=0xFEE75C)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="givexp", description="Donner de l'XP à un membre")
    @app_commands.describe(membre="Le membre", xp="Quantité d'XP")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def givexp(self, interaction: discord.Interaction, membre: discord.Member, xp: int):
        cursor = await self.bot.db.execute(
            "SELECT xp, level FROM level_data WHERE user_id = ? AND guild_id = ?",
            (membre.id, interaction.guild.id)
        )
        row = await cursor.fetchone()
        if row:
            new_xp = row[0] + xp
            new_level = self.calculate_level(new_xp)
            await self.bot.db.execute(
                "UPDATE level_data SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?",
                (new_xp, new_level, membre.id, interaction.guild.id)
            )
        else:
            new_level = self.calculate_level(xp)
            await self.bot.db.execute(
                "INSERT INTO level_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                (membre.id, interaction.guild.id, xp, new_level)
            )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ +{xp} XP donné à {membre.mention}. Total: {new_xp if row else xp}")

async def setup(bot):
    await bot.add_cog(Levels(bot))
