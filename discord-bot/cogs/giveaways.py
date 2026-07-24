import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == "🎉":
            cursor = await self.bot.db.execute(
                "SELECT id, winner_count, prize FROM giveaways WHERE message_id = ? AND guild_id = ? AND ended = 0",
                (payload.message_id, payload.guild_id)
            )
            giveaway = await cursor.fetchone()
            if giveaway:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                users = [u async for u in reaction.users() if not u.bot]
                # Store participants

    @app_commands.command(name="giveaway", description="Lancer un giveaway")
    @app_commands.describe(duree="Durée en minutes", prix="Le prix", gagnants="Nombre de gagnants")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway(self, interaction: discord.Interaction, duree: int, prix: str, gagnants: int = 1):
        await interaction.response.defer()
        end_time = datetime.utcnow() + timedelta(minutes=duree)
        embed = discord.Embed(
            title="🎉 GIVEAWAY! 🎉",
            description=f"**Prix:** {prix}\n**Gagnants:** {gagnants}\n**Se termine:** <t:{int(end_time.timestamp())}:R>\n\nRéagis avec 🎉 pour participer!",
            color=0xFFD700,
            timestamp=end_time
        )
        embed.set_footer(text=f"Lancé par {interaction.user} | {interaction.guild.name}")
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        msg = await interaction.followup.send(embed=embed)
        await msg.add_reaction("🎉")
        await self.bot.db.execute(
            "INSERT INTO giveaways (message_id, channel_id, guild_id, prize, winner_count, host_id, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg.id, interaction.channel.id, interaction.guild.id, prix, gagnants, interaction.user.id, end_time.isoformat())
        )
        await self.bot.db.commit()

    @app_commands.command(name="giveaway-end", description="Terminer un giveaway")
    @app_commands.describe(message_id="ID du message du giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_end(self, interaction: discord.Interaction, message_id: str):
        cursor = await self.bot.db.execute(
            "SELECT channel_id, prize, winner_count, id FROM giveaways WHERE message_id = ? AND guild_id = ? AND ended = 0",
            (int(message_id), interaction.guild.id)
        )
        giveaway = await cursor.fetchone()
        if not giveaway:
            return await interaction.response.send_message("❌ Giveaway introuvable ou déjà terminé.", ephemeral=True)
        await self.bot.db.execute("UPDATE giveaways SET ended = 1 WHERE id = ?", (giveaway[3],))
        await self.bot.db.commit()
        channel = self.bot.get_channel(giveaway[0])
        try:
            message = await channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            return await interaction.response.send_message("❌ Aucune réaction trouvée.", ephemeral=True)
        users = [u async for u in reaction.users() if not u.bot]
        if not users:
            return await interaction.response.send_message("❌ Aucun participant.", ephemeral=True)
        winners = random.sample(users, min(giveaway[2], len(users)))
        winner_mentions = ", ".join([w.mention for w in winners])
        embed = discord.Embed(
            title="🎉 GIVEAWAY TERMINÉ! 🎉",
            description=f"**Prix:** {giveaway[1]}\n**Gagnant(s):** {winner_mentions}",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)
        await channel.send(f"🎉 Félicitations {winner_mentions}! Tu as gagné **{giveaway[1]}**!")

    @app_commands.command(name="giveaway-reroll", description="Relancer un giveaway pour un nouveau gagnant")
    @app_commands.describe(message_id="ID du message du giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        channel = interaction.channel
        try:
            message = await channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            return await interaction.response.send_message("❌ Aucune réaction trouvée.", ephemeral=True)
        users = [u async for u in reaction.users() if not u.bot]
        if not users:
            return await interaction.response.send_message("❌ Aucun participant.", ephemeral=True)
        winner = random.choice(users)
        await interaction.response.send_message(f"🎉 Nouveau gagnant: {winner.mention}!")

    @commands.tasks.loop(seconds=30)
    async def check_giveaways(self):
        cursor = await self.bot.db.execute(
            "SELECT id, message_id, channel_id, guild_id, prize, winner_count FROM giveaways WHERE ended = 0 AND end_time <= ?",
            (datetime.utcnow().isoformat(),)
        )
        ended = await cursor.fetchall()
        for g in ended:
            channel = self.bot.get_channel(g[2])
            if not channel:
                continue
            try:
                message = await channel.fetch_message(g[1])
            except:
                continue
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                continue
            users = [u async for u in reaction.users() if not u.bot]
            if users:
                winners = random.sample(users, min(g[5], len(users)))
                winner_mentions = ", ".join([w.mention for w in winners])
                embed = discord.Embed(
                    title="🎉 GIVEAWAY TERMINÉ! 🎉",
                    description=f"**Prix:** {g[4]}\n**Gagnant(s):** {winner_mentions}",
                    color=0xFFD700
                )
                await channel.send(embed=embed)
                await channel.send(f"🎉 Félicitations {winner_mentions}! Tu as gagné **{g[4]}**!")
            await self.bot.db.execute("UPDATE giveaways SET ended = 1 WHERE id = ?", (g[0],))
        await self.bot.db.commit()

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
