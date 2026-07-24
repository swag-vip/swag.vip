import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket-setup", description="Configurer le système de tickets")
    @app_commands.describe(channel="Le salon d'envoi", categorie="La catégorie des tickets")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, categorie: discord.CategoryChannel):
        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description="Clique sur le bouton ci-dessous pour ouvrir un ticket.",
            color=0x5865F2
        )
        embed.set_footer(text=f"{interaction.guild.name} • Support")
        button = TicketButton(self.bot, categorie.id)
        view = discord.ui.View(timeout=None)
        view.add_item(button)
        await channel.send(embed=embed, view=view)
        cursor = await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "ticket_category", str(categorie.id))
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Système de tickets configuré dans {channel.mention}", ephemeral=True)

    @app_commands.command(name="ticket-close", description="Fermer le ticket actuel")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def ticket_close(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT id, user_id FROM tickets WHERE channel_id = ? AND guild_id = ? AND status = 'open'",
            (interaction.channel.id, interaction.guild.id)
        )
        ticket = await cursor.fetchone()
        if not ticket:
            return await interaction.response.send_message("❌ Ce n'est pas un ticket actif.", ephemeral=True)
        await self.bot.db.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = ?",
            (ticket[0],)
        )
        await self.bot.db.commit()
        user = self.bot.get_user(ticket[1])
        embed = discord.Embed(title="🎫 Ticket Fermé", description=f"Fermé par {interaction.user.mention}", color=0xED4245)
        embed.set_footer(text=f"Ticket #{ticket[0]}")
        await interaction.response.send_message(embed=embed)
        try:
            await user.send(f"🎫 Ton ticket sur **{interaction.guild.name}** a été fermé par {interaction.user}.")
        except:
            pass

    @app_commands.command(name="ticket-add", description="Ajouter un membre au ticket")
    @app_commands.describe(membre="Le membre à ajouter")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def ticket_add(self, interaction: discord.Interaction, membre: discord.Member):
        overwrite = interaction.channel.overwrites_for(membre)
        overwrite.send_messages = True
        overwrite.view_channel = True
        await interaction.channel.set_permissions(membre, overwrite=overwrite)
        await interaction.response.send_message(f"✅ {membre.mention} ajouté au ticket.")

    @app_commands.command(name="ticket-remove", description="Retirer un membre du ticket")
    @app_commands.describe(membre="Le membre à retirer")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def ticket_remove(self, interaction: discord.Interaction, membre: discord.Member):
        overwrite = interaction.channel.overwrites_for(membre)
        overwrite.send_messages = False
        overwrite.view_channel = False
        await interaction.channel.set_permissions(membre, overwrite=overwrite)
        await interaction.response.send_message(f"✅ {membre.mention} retiré du ticket.")

    @app_commands.command(name="ticket-list", description="Lister les tickets actifs")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def ticket_list(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT id, user_id, channel_id, status, created_at FROM tickets WHERE guild_id = ? ORDER BY created_at DESC LIMIT 25",
            (interaction.guild.id,)
        )
        tickets = await cursor.fetchall()
        if not tickets:
            return await interaction.response.send_message("❌ Aucun ticket.", ephemeral=True)
        desc = ""
        for t in tickets:
            status = "🟢" if t[3] == "open" else "🔴"
            desc += f"{status} Ticket #{t[0]} — <@{t[1]}> — {t[4]}\n"
        embed = discord.Embed(title="🎫 Tickets", description=desc, color=0x5865F2)
        await interaction.response.send_message(embed=embed)

class TicketButton(discord.ui.Button):
    def __init__(self, bot, category_id):
        super().__init__(label="Ouvrir un Ticket", style=discord.ButtonStyle.green, custom_id="ticket_open")
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT id FROM tickets WHERE user_id = ? AND guild_id = ? AND status = 'open'",
            (interaction.user.id, interaction.guild.id)
        )
        existing = await cursor.fetchone()
        if existing:
            return await interaction.response.send_message("❌ Tu as déjà un ticket ouvert.", ephemeral=True)
        category = interaction.guild.get_channel(self.category_id)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        await self.bot.db.execute(
            "INSERT INTO tickets (channel_id, guild_id, user_id) VALUES (?, ?, ?)",
            (channel.id, interaction.guild.id, interaction.user.id)
        )
        await self.bot.db.commit()
        embed = discord.Embed(
            title=f"🎫 Ticket #{interaction.user.name}",
            description=f"Bonjour {interaction.user.mention}! Décris ton problème.\nUn membre du staff va t'aider.",
            color=0x57F287
        )
        embed.set_footer(text="Ferme avec /ticket-close")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"🎫 Ticket ouvert: {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
