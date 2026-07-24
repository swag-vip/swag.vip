import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setlogs", description="Configurer le salon de logs")
    @app_commands.describe(channel="Le salon de logs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setlogs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "logs_channel", str(channel.id))
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Salon de logs configuré: {channel.mention}")

    async def get_log_channel(self, guild_id):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'logs_channel'",
            (guild_id,)
        )
        row = await cursor.fetchone()
        if row:
            return self.bot.get_channel(int(row[0]))
        return None

    @app_commands.command(name="testlogs", description="Tester le système de logs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def testlogs(self, interaction: discord.Interaction):
        channel = await self.get_log_channel(interaction.guild.id)
        if not channel:
            return await interaction.response.send_message("❌ Salon de logs non configuré.", ephemeral=True)
        embed = discord.Embed(
            title="📋 Test de Log",
            description="Le système de logs fonctionne!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Testé par {interaction.user}")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Message de test envoyé dans {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        channel = await self.get_log_channel(message.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🗑️ Message supprimé",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=message.author.mention, inline=True)
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenu", value=message.content[:1024] if message.content else "Aucun contenu", inline=False)
        embed.set_footer(text=f"ID: {message.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        channel = await self.get_log_channel(before.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="✏️ Message modifié",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=before.author.mention, inline=True)
        embed.add_field(name="Salon", value=before.channel.mention, inline=True)
        embed.add_field(name="Avant", value=before.content[:1024] or "Aucun contenu", inline=False)
        embed.add_field(name="Après", value=after.content[:1024] or "Aucun contenu", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = await self.get_log_channel(guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🔨 Membre banni",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{user} ({user.id})", inline=True)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = await self.get_log_channel(guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="✅ Membre débanni",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{user} ({user.id})", inline=True)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_log_channel(member.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="📥 Membre rejoint",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Compte créé", value=discord.utils.format_dt(member.created_at, 'R'), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.get_log_channel(member.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="📤 Membre quitté",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{member} ({member.id})", inline=True)
        roles = ", ".join([r.name for r in member.roles[1:][:10]])
        embed.add_field(name="Rôles", value=roles or "Aucun", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild is None:
            return
        channel = await self.get_log_channel(before.guild.id)
        if not channel:
            return
        changes = []
        if before.nick != after.nick:
            changes.append(f"Surnom: `{before.nick}` → `{after.nick}`")
        if before.roles != after.roles:
            added = [r.name for r in after.roles if r not in before.roles]
            removed = [r.name for r in before.roles if r not in after.roles]
            if added:
                changes.append(f"Rôles ajoutés: {', '.join(added)}")
            if removed:
                changes.append(f"Rôles retirés: {', '.join(removed)}")
        if before.name != after.name:
            changes.append(f"Nom: `{before.name}` → `{after.name}`")
        if changes:
            embed = discord.Embed(
                title="📝 Membre modifié",
                description="\n".join(changes),
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        channel = await self.get_log_channel(member.guild.id)
        if not channel:
            return
        if after.channel:
            embed = discord.Embed(
                title="🔊 Vocal: Connexion",
                description=f"{member.mention} a rejoint {after.channel.mention}",
                color=0x57F287,
                timestamp=datetime.utcnow()
            )
        elif before.channel:
            embed = discord.Embed(
                title="🔊 Vocal: Déconnexion",
                description=f"{member.mention} a quitté {before.channel.mention}",
                color=0xED4245,
                timestamp=datetime.utcnow()
            )
        else:
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_role_create(self, role):
        channel = await self.get_log_channel(role.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🎭 Rôle créé",
            description=f"{role.mention} ({role.id})",
            color=role.color,
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_role_delete(self, role):
        channel = await self.get_log_channel(role.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🎭 Rôle supprimé",
            description=f"`{role.name}` ({role.id})",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        if not channel.guild:
            return
        log_ch = await self.get_log_channel(channel.guild.id)
        if not log_ch:
            return
        embed = discord.Embed(
            title="📢 Salon créé",
            description=f"{channel.mention} ({channel.id})",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_channel_delete(self, channel):
        if not channel.guild:
            return
        log_ch = await self.get_log_channel(channel.guild.id)
        if not log_ch:
            return
        embed = discord.Embed(
            title="📢 Salon supprimé",
            description=f"`{channel.name}` ({channel.id})",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        await log_ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
