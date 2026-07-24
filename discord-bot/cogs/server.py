import discord
from discord.ext import commands
from discord import app_commands
import json

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Setup rapide du serveur")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Setup du Serveur",
            description="Choisis ce que tu veux configurer:",
            color=0x5865F2
        )
        embed.add_field(name="1. 📋 Rôles", value="Créer les rôles de base (Membre, VIP, Staff)", inline=False)
        embed.add_field(name="2. 📢 Salons", value="Créer les salons essentiels", inline=False)
        embed.add_field(name="3. 🔨 Modération", value="Configurer les permissions de modération", inline=False)
        embed.add_field(name="4. 👋 Welcome", value="Configurer le système de bienvenue", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="create-roles", description="Créer les rôles de base du serveur")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create_roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        roles_data = [
            ("🏷️ Membre", 0x99AAB5, False),
            ("⭐ VIP", 0xF1C40F, False),
            ("🛡️ Staff", 0xE74C3C, False),
            ("👑 Admin", 0xFF0000, False),
            ("🤖 Bot", 0x5865F2, True),
            ("🔇 Muted", 0x747F8D, False),
        ]
        created = []
        for name, color, hoist in roles_data:
            existing = discord.utils.get(interaction.guild.roles, name=name)
            if not existing:
                role = await interaction.guild.create_role(
                    name=name, color=discord.Color(color), hoist=hoist,
                    reason=f"Setup par {interaction.user}"
                )
                created.append(role.mention)
        if created:
            await interaction.followup.send(f"✅ Rôles créés: {', '.join(created)}")
        else:
            await interaction.followup.send("ℹ️ Tous les rôles existent déjà.")

    @app_commands.command(name="create-channels", description="Créer les salons essentiels")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def create_channels(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channels_data = [
            ("rules", "texte", "📜 Règles"),
            ("annonces", "texte", "📢 Annonces"),
            ("general", "texte", "💬 Général"),
            ("bot-commands", "texte", "🤖 Commandes Bot"),
            ("support", "texte", "🎫 Support"),
            ("vip", "texte", "⭐ VIP"),
        ]
        created = []
        for name, ch_type, display in channels_data:
            existing = discord.utils.get(interaction.guild.text_channels, name=name)
            if not existing:
                ch = await interaction.guild.create_text_channel(name, topic=display)
                created.append(ch.mention)
        voice = discord.utils.get(interaction.guild.voice_channels, name="General")
        if not voice:
            ch = await interaction.guild.create_voice_channel("🔊 Général")
            created.append(ch.mention)
        if created:
            await interaction.followup.send(f"✅ Salons créés: {', '.join(created)}")
        else:
            await interaction.followup.send("ℹ️ Tous les salons existent déjà.")

    @app_commands.command(name="massrole", description="Ajouter un rôle à tous les membres")
    @app_commands.describe(role="Le rôle à donner")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def massrole(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
        await interaction.response.defer()
        count = 0
        for member in interaction.guild.members:
            if role not in member.roles and not member.bot:
                try:
                    await member.add_roles(role)
                    count += 1
                except:
                    pass
        await interaction.followup.send(f"✅ Rôle **{role.name}** donné à **{count}** membres.")

    @app_commands.command(name="massunrole", description="Retirer un rôle à tous les membres")
    @app_commands.describe(role="Le rôle à retirer")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def massunrole(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
        await interaction.response.defer()
        count = 0
        for member in interaction.guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    count += 1
                except:
                    pass
        await interaction.followup.send(f"✅ Rôle **{role.name}** retiré à **{count}** membres.")

    @app_commands.command(name="backup", description="Sauvegarder les rôles du serveur")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def backup(self, interaction: discord.Interaction):
        roles = []
        for role in interaction.guild.roles:
            if role != interaction.guild.default_role:
                roles.append({
                    "name": role.name,
                    "color": str(role.color),
                    "permissions": role.permissions.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position
                })
        data = json.dumps(roles, indent=2, ensure_ascii=False)
        embed = discord.Embed(title="💾 Backup des rôles", description=f"```json\n{data[:1900]}\n```", color=0x57F287)
        embed.set_footer(text=f"{len(roles)} rôles sauvegardés")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="server-stats", description="Statistiques détaillées du serveur")
    async def server_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"📊 Stats de {guild.name}", color=0x5865F2)
        embed.add_field(name="👥 Membres total", value=str(guild.member_count))
        embed.add_field(name="🤖 Bots", value=str(sum(1 for m in guild.members if m.bot)))
        embed.add_field(name="👤 Humains", value=str(sum(1 for m in guild.members if not m.bot)))
        text = sum(1 for c in guild.channels if isinstance(c, discord.TextChannel))
        voice = sum(1 for c in guild.channels if isinstance(c, discord.VoiceChannel))
        embed.add_field(name="💬 Salons texte", value=str(text))
        embed.add_field(name="🔊 Salons vocal", value=str(voice))
        embed.add_field(name="📁 Catégories", value=str(len(guild.categories)))
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)))
        embed.add_field(name="🎭 Rôles", value=str(len(guild.roles) - 1))
        embed.add_field(name="🚀 Boosts", value=str(guild.premium_subscription_count))
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        embed.add_field(name="🟢 En ligne", value=str(online))
        embed.add_field(name="🟡 Idle", value=str(idle))
        embed.add_field(name="🔴 DND", value=str(dnd))
        embed.add_field(name="⚫ Hors-ligne", value=str(offline))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server-audit", description="Vérifier les permissions du serveur")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def server_audit(self, interaction: discord.Interaction):
        issues = []
        if not guild.me.guild_permissions.administrator:
            issues.append("⚠️ Le bot n'a pas la permission Admin")
        if not guild.me.guild_permissions.ban_members:
            issues.append("⚠️ Le bot ne peut pas bannir")
        if not guild.me.guild_permissions.kick_members:
            issues.append("⚠️ Le bot ne peut pas kick")
        if not guild.me.guild_permissions.manage_channels:
            issues.append("⚠️ Le bot ne peut pas gérer les salons")
        if not guild.me.guild_permissions.manage_roles:
            issues.append("⚠️ Le bot ne peut pas gérer les rôles")
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            issues.append("⚠️ Rôle 'Muted' absent")

        embed = discord.Embed(title="🔍 Audit du Serveur", color=0x57F287 if not issues else 0xFEE75C)
        if issues:
            embed.description = "\n".join(issues)
        else:
            embed.description = "✅ Tout est en ordre!"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="permissions", description="Voir les permissions d'un membre")
    @app_commands.describe(membre="Le membre")
    async def permissions(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        perms = [p[0].replace('_', ' ').title() for p in membre.guild_permissions if p[1]]
        embed = discord.Embed(title=f"🔑 Permissions de {membre.name}", color=membre.color)
        embed.description = "\n".join([f"✅ {p}" for p in perms]) if perms else "❌ Aucune permission spéciale"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bans", description="Liste des membres bannis")
    @app_commands.checks.has_permissions(ban_members=True)
    async def bans(self, interaction: discord.Interaction):
        bans = [entry async for entry in interaction.guild.bans()]
        if not bans:
            return await interaction.response.send_message("❌ Aucun membre banni.", ephemeral=True)
        desc = "\n".join([f"• {b.user} ({b.user.id}) — {b.reason or 'Aucune raison'}" for b in bans[:25]])
        embed = discord.Embed(title=f"🔨 Membres bannis ({len(bans)})", description=desc, color=0xED4245)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="prune", description="Supprimer les membres inactifs")
    @app_commands.describe(jours="Jours d'inactivité (défaut: 30)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def prune(self, interaction: discord.Interaction, jours: int = 30):
        await interaction.response.defer()
        pruned = await interaction.guild.prune_members(days=jours, reason=f"Prune par {interaction.user}")
        await interaction.followup.send(f"✅ **{pruned}** membres inactifs supprimés (>{jours} jours).")

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
