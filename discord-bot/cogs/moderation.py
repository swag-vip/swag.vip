import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bannir un membre du serveur")
    @app_commands.describe(membre="Le membre à bannir", raison="Raison du ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas te bannir toi-même.", ephemeral=True)
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce membre a un rôle supérieur ou égal au tien.", ephemeral=True)
        try:
            await membre.send(f"🔨 Tu as été banni de **{interaction.guild.name}** pour: {raison}")
        except:
            pass
        await membre.ban(reason=raison, delete_message_days=7)
        embed = discord.Embed(title="🔨 Membre banni", color=0xED4245)
        embed.add_field(name="Membre", value=f"{membre.mention}", inline=True)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Débannir un membre")
    @app_commands.describe(user_id="ID de l'utilisateur à débannir")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            embed = discord.Embed(title="✅ Membre débanni", color=0x57F287)
            embed.add_field(name="Utilisateur", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("❌ Utilisateur non trouvé ou pas banni.", ephemeral=True)

    @app_commands.command(name="kick", description="Expulser un membre du serveur")
    @app_commands.describe(membre="Le membre à expulser", raison="Raison de l'expulsion")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas t'expulser toi-même.", ephemeral=True)
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce membre a un rôle supérieur ou égal au tien.", ephemeral=True)
        try:
            await membre.send(f"🚪 Tu as été expulsé de **{interaction.guild.name}** pour: {raison}")
        except:
            pass
        await membre.kick(reason=raison)
        embed = discord.Embed(title="🚪 Membre expulsé", color=0xFEE75C)
        embed.add_field(name="Membre", value=f"{membre.mention}", inline=True)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute", description="Rendre muet un membre")
    @app_commands.describe(membre="Le membre à mute", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, duree: int = 10, raison: str = "Aucune raison"):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas te mute toi-même.", ephemeral=True)
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce membre a un rôle supérieur ou égal au tien.", ephemeral=True)
        duration = timedelta(minutes=duree)
        await membre.timeout(duration, reason=raison)
        embed = discord.Embed(title="🔇 Membre rendu muet", color=0xFEE75C)
        embed.add_field(name="Membre", value=membre.mention, inline=True)
        embed.add_field(name="Durée", value=f"{duree} minutes", inline=True)
        embed.add_field(name="Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="Retirer le silence d'un membre")
    @app_commands.describe(membre="Le membre à unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None, reason="Unmute par modérateur")
        embed = discord.Embed(title="🔊 Membre unmute", color=0x57F287)
        embed.add_field(name="Membre", value=membre.mention, inline=True)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(membre="Le membre à warn", raison="Raison du warn")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas te warn toi-même.", ephemeral=True)
        await self.bot.db.execute(
            "INSERT INTO warns (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (membre.id, interaction.guild.id, interaction.user.id, raison)
        )
        await self.bot.db.commit()
        cursor = await self.bot.db.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id = ? AND guild_id = ?",
            (membre.id, interaction.guild.id)
        )
        count = (await cursor.fetchone())[0]
        embed = discord.Embed(title="⚠️ Membre averti", color=0xFEE75C)
        embed.add_field(name="Membre", value=membre.mention, inline=True)
        embed.add_field(name="Warns total", value=str(count), inline=True)
        embed.add_field(name="Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)
        try:
            await membre.send(f"⚠️ Tu as reçu un avertissement sur **{interaction.guild.name}** pour: {raison}\nTotal: {count} warns")
        except:
            pass

    @app_commands.command(name="unwarn", description="Retirer un warn à un membre")
    @app_commands.describe(membre="Le membre", warn_id="ID du warn à supprimer")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unwarn(self, interaction: discord.Interaction, membre: discord.Member, warn_id: int):
        cursor = await self.bot.db.execute(
            "SELECT id FROM warns WHERE id = ? AND user_id = ? AND guild_id = ?",
            (warn_id, membre.id, interaction.guild.id)
        )
        warn = await cursor.fetchone()
        if not warn:
            return await interaction.response.send_message("❌ Warn introuvable.", ephemeral=True)
        await self.bot.db.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Warn #{warn_id} supprimé pour {membre.mention}")

    @app_commands.command(name="warnings", description="Voir les warns d'un membre")
    @app_commands.describe(membre="Le membre à vérifier")
    async def warnings(self, interaction: discord.Interaction, membre: discord.Member):
        cursor = await self.bot.db.execute(
            "SELECT id, moderator_id, reason, created_at FROM warns WHERE user_id = ? AND guild_id = ? ORDER BY created_at DESC",
            (membre.id, interaction.guild.id)
        )
        warns = await cursor.fetchall()
        if not warns:
            return await interaction.response.send_message(f"ℹ️ {membre.mention} n'a aucun avertissement.", ephemeral=True)
        embed = discord.Embed(title=f"⚠️ Warns de {membre.name}", color=0xFEE75C, timestamp=discord.utils.utcnow())
        for w in warns:
            mod = interaction.guild.get_member(w[1])
            mod_name = mod.mention if mod else "Inconnu"
            embed.add_field(
                name=f"Warn #{w[0]}",
                value=f"**Modérateur:** {mod_name}\n**Raison:** {w[2]}\n**Date:** {w[3]}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Supprimer des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, nombre: int = 10):
        if nombre < 1 or nombre > 100:
            return await interaction.response.send_message("❌ Nombre entre 1 et 100.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ {len(deleted)} messages supprimés.", ephemeral=True)

    @app_commands.command(name="slowmode", description="Définir le slowmode d'un salon")
    @app_commands.describe(duree="Durée en secondes (0 = désactiver)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, duree: int = 0):
        if duree < 0 or duree > 21600:
            return await interaction.response.send_message("❌ Durée entre 0 et 21600 secondes.", ephemeral=True)
        await interaction.channel.edit(slowmode_delay=duree)
        if duree == 0:
            await interaction.response.send_message("✅ Slowmode désactivé.")
        else:
            await interaction.response.send_message(f"✅ Slowmode défini à **{duree}** secondes.")

    @app_commands.command(name="lock", description="Verrouiller un salon")
    @app_commands.describe(raison="Raison du verrouillage")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, raison: str = "Aucune raison"):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=raison)
        embed = discord.Embed(title="🔒 Salon verrouillé", color=0xED4245)
        embed.add_field(name="Raison", value=raison)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlock", description="Déverrouiller un salon")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Salon déverrouillé.")

    @app_commands.command(name="nuke", description="Recréer un salon (supprime tout)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        channel = interaction.channel
        new_channel = await channel.clone(reason=f"Nuke par {interaction.user}")
        await channel.delete()
        embed = discord.Embed(title="💣 Salon nuké", color=0xED4245, description=f"Salon recréé par {interaction.user.mention}")
        await new_channel.send(embed=embed)

    @app_commands.command(name="timeout", description="Mettre en timeout un membre")
    @app_commands.describe(membre="Le membre", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, membre: discord.Member, duree: int, raison: str = "Aucune raison"):
        duration = timedelta(minutes=duree)
        await membre.timeout(duration, reason=raison)
        embed = discord.Embed(title="⏰ Timeout", color=0xFEE75C)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Durée", value=f"{duree} min")
        embed.add_field(name="Raison", value=raison)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="softban", description="Softban un membre (ban + unban pour supprimer les messages)")
    @app_commands.describe(membre="Le membre", raison="Raison")
    @app_commands.checks.has_permissions(ban_members=True)
    async def softban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        await membre.ban(reason=raison, delete_message_days=7)
        await interaction.guild.unban(membre)
        embed = discord.Embed(title="🔨 Softban", color=0xED4245)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Raison", value=raison)
        embed.set_footer(text="Les 7 derniers jours de messages ont été supprimés")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="massban", description="Bannir plusieurs membres d'un coup")
    @app_commands.describe(ids="IDs des membres séparés par des espaces", raison="Raison")
    @app_commands.checks.has_permissions(ban_members=True)
    async def massban(self, interaction: discord.Interaction, ids: str, raison: str = "Mass ban"):
        await interaction.response.defer(ephemeral=True)
        banned = 0
        failed = 0
        for user_id in ids.split():
            try:
                user = await self.bot.fetch_user(int(user_id))
                await interaction.guild.ban(user, reason=raison, delete_message_days=7)
                banned += 1
            except:
                failed += 1
        await interaction.followup.send(f"✅ {banned} membres bannis. ❌ {failed} échecs.")

    @app_commands.command(name="nick", description="Changer le surnom d'un membre")
    @app_commands.describe(membre="Le membre", nickname="Nouveau surnom")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick(self, interaction: discord.Interaction, membre: discord.Member, nickname: str):
        await membre.edit(nick=nickname)
        await interaction.response.send_message(f"✅ Surnom de {membre.mention} changé en **{nickname}**")

    @app_commands.command(name="deafen", description="Rendre sourd un membre")
    @app_commands.describe(membre="Le membre")
    @app_commands.checks.has_permissions(deafen_members=True)
    async def deafen(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.edit(deafen=True)
        await interaction.response.send_message(f"🔇 {membre.mention} est maintenant sourd.")

    @app_commands.command(name="undeafen", description="Retirer la surdité d'un membre")
    @app_commands.describe(membre="Le membre")
    @app_commands.checks.has_permissions(deafen_members=True)
    async def undeafen(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.edit(deafen=False)
        await interaction.response.send_message(f"🔊 {membre.mention} n'est plus sourd.")

    @app_commands.command(name="move", description="Déplacer un membre dans un salon vocal")
    @app_commands.describe(membre="Le membre", channel="Le salon vocal")
    @app_commands.checks.has_permissions(move_members=True)
    async def move(self, interaction: discord.Interaction, membre: discord.Member, channel: discord.VoiceChannel):
        if membre.voice:
            await membre.move_to(channel)
            await interaction.response.send_message(f"✅ {membre.mention} déplacé vers {channel.mention}")
        else:
            await interaction.response.send_message("❌ Ce membre n'est pas dans un salon vocal.", ephemeral=True)

    @app_commands.command(name="disconnect", description="Déconnecter un membre d'un salon vocal")
    @app_commands.describe(membre="Le membre")
    @app_commands.checks.has_permissions(move_members=True)
    async def disconnect(self, interaction: discord.Interaction, membre: discord.Member):
        if membre.voice:
            await membre.move_to(None)
            await interaction.response.send_message(f"✅ {membre.mention} déconnecté.")
        else:
            await interaction.response.send_message("❌ Ce membre n'est pas dans un salon vocal.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
