import discord
from discord.ext import commands
from discord import app_commands

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactionrole", description="Créer un système de reaction role")
    @app_commands.describe(
        channel="Le salon où envoyer le message",
        role="Le rôle à donner",
        emoji="L'emoji à utiliser",
        titre="Titre du message",
        description="Description du message"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole(
        self, interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role,
        emoji: str,
        titre: str = "Reaction Role",
        description: str = "Clique sur l'emoji pour obtenir le rôle!"
    ):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal au tien.", ephemeral=True)
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal à celui du bot.", ephemeral=True)
        embed = discord.Embed(title=titre, description=description, color=role.color or discord.Color.blue())
        embed.set_footer(text=f"{interaction.guild.name} • Reaction Role")
        msg = await channel.send(embed=embed)
        await msg.add_reaction(emoji)
        await self.bot.db.execute(
            "INSERT INTO reaction_roles (message_id, channel_id, guild_id, role_id, emoji) VALUES (?, ?, ?, ?, ?)",
            (msg.id, channel.id, interaction.guild.id, role.id, emoji)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Reaction role créé dans {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        cursor = await self.bot.db.execute(
            "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (payload.message_id, str(payload.emoji))
        )
        row = await cursor.fetchone()
        if row:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(row[0])
            if role:
                try:
                    await payload.member.add_roles(role, reason="Reaction Role")
                except:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        cursor = await self.bot.db.execute(
            "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (payload.message_id, str(payload.emoji))
        )
        row = await cursor.fetchone()
        if row:
            role = guild.get_role(row[0])
            if role:
                try:
                    await member.remove_roles(role, reason="Reaction Role")
                except:
                    pass

    @app_commands.command(name="reactionrole-delete", description="Supprimer un reaction role")
    @app_commands.describe(message_id="ID du message du reaction role")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_delete(self, interaction: discord.Interaction, message_id: str):
        cursor = await self.bot.db.execute(
            "SELECT emoji, channel_id FROM reaction_roles WHERE message_id = ? AND guild_id = ?",
            (int(message_id), interaction.guild.id)
        )
        rows = await cursor.fetchall()
        if not rows:
            return await interaction.response.send_message("❌ Reaction role introuvable.", ephemeral=True)
        for r in rows:
            channel = self.bot.get_channel(r[1])
            if channel:
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.clear_reaction(r[0])
                except:
                    pass
        await self.bot.db.execute("DELETE FROM reaction_roles WHERE message_id = ?", (int(message_id),))
        await self.bot.db.commit()
        await interaction.response.send_message("✅ Reaction role supprimé.")

    @app_commands.command(name="reactionrole-list", description="Lister les reaction roles actifs")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_list(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT message_id, role_id, emoji FROM reaction_roles WHERE guild_id = ?",
            (interaction.guild.id,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return await interaction.response.send_message("❌ Aucun reaction role.", ephemeral=True)
        desc = ""
        for msg_id, role_id, emoji in rows:
            role = interaction.guild.get_role(role_id)
            role_name = role.mention if role else "Supprimé"
            desc += f"{emoji} → {role_name} (Message: {msg_id})\n"
        embed = discord.Embed(title="🎭 Reaction Roles", description=desc, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
