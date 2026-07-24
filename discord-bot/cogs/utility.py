import discord
from discord.ext import commands
from discord import app_commands
import platform
import psutil
import os
import asyncio
from datetime import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Afficher la liste des commandes")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📚 Liste des commandes", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
        embed.add_field(name="🔨 Modération", value="`ban`, `unban`, `kick`, `mute`, `unmute`, `warn`, `unwarn`, `warnings`, `purge`, `slowmode`, `lock`, `unlock`, `nuke`, `timeout`, `softban`, `massban`, `nick`, `deafen`, `undeafen`, `move`, `disconnect`", inline=False)
        embed.add_field(name="🛠️ Utilité", value="`help`, `serverinfo`, `userinfo`, `avatar`, `banner`, `membercount`, `servericon`, `serverbanner`, `invitecount`, `ping`, `uptime`, `botinfo`, `roleinfo`, `channelinfo`, `created`, `joined`, `roles`, `boosts`, `online`, `id`, `discriminator`", inline=False)
        embed.add_field(name="🎵 Gestion Rôles", value="`addrole`, `removerole`, `createrole`, `deleterole`, `editrole`, `roleall`, `rolemembers`, `roles`, `color`", inline=False)
        embed.add_field(name="📡 Gestion Salons", value="`createchannel`, `deletechannel`, `renamechannel`, `clone`, `slowmode`, `lock`, `unlock`, `nsfw`, `topic`, `channelinfo`", inline=False)
        embed.add_field(name="📈 Niveaux/XP", value="`rank`, `leaderboard`, `setxp`, `resetxp`, `xprewards`", inline=False)
        embed.add_field(name="🎫 Tickets", value="`ticket-setup`, `ticket-close`, `ticket-add`, `ticket-remove`", inline=False)
        embed.add_field(name="🎉 Giveaways", value="`giveaway`, `giveaway-end`, `giveaway-reroll`", inline=False)
        embed.add_field(name="🎭 Reaction Roles", value="`reactionrole`", inline=False)
        embed.add_field(name="📝 Logs", value="`setlogs`, `testlogs`", inline=False)
        embed.add_field(name="🤖 Auto-Mod", value="`automod-setup`, `automod-config`, `antispam`, `antilink`, `wordfilter`, `autoresponse`", inline=False)
        embed.add_field(name="👋 Welcome/Goodbye", value="`setwelcome`, `setgoodbye`, `autorole`, `testwelcome`", inline=False)
        embed.add_field(name="🎉 Fun", value="`8ball`, `coinflip`, `dice`, `say`, `reverse`, `mock`, `rate`, `ship`, `meme`, `joke`, `poll`", inline=False)
        embed.add_field(name="🎨 Embeds", value="`embed`, `embedbuilder`, `announce`", inline=False)
        embed.set_footer(text=f"Total: 100+ commandes | Prefix: {self.bot.config['prefix']}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Afficher les informations du serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"📊 {guild.name}", color=0x5865F2, timestamp=discord.utils.utcnow())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention if guild.owner else "Inconnu", inline=True)
        embed.add_field(name="🆔 ID", value=str(guild.id), inline=True)
        embed.add_field(name="📅 Créé le", value=discord.utils.format_dt(guild.created_at, 'D'), inline=True)
        embed.add_field(name="👥 Membres", value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Salons", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)
        embed.add_field(name="🚀 Boosts", value=str(guild.premium_subscription_count), inline=True)
        embed.add_field(name="🔒 Vérification", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="🌍 Région", value=str(guild.region) if hasattr(guild, 'region') else "Auto", inline=True)
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        embed.add_field(name="🟢 En ligne", value=str(online), inline=True)
        text_channels = sum(1 for c in guild.channels if isinstance(c, discord.TextChannel))
        voice_channels = sum(1 for c in guild.channels if isinstance(c, discord.VoiceChannel))
        embed.add_field(name="💬 Texte", value=str(text_channels), inline=True)
        embed.add_field(name="🔊 Vocal", value=str(voice_channels), inline=True)
        roles = len(guild.roles) - 1
        embed.add_field(name="🎭 Rôles", value=str(roles), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Afficher les informations d'un membre")
    @app_commands.describe(membre="Le membre à inspecter")
    async def userinfo(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"👤 {membre}", color=membre.color, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="🆔 ID", value=str(membre.id), inline=True)
        embed.add_field(name="📛 Nom", value=str(membre), inline=True)
        embed.add_field(name="🎨 Couleur", value=str(membre.color), inline=True)
        embed.add_field(name="📅 Compte créé", value=discord.utils.format_dt(membre.created_at, 'D'), inline=True)
        embed.add_field(name="📥 A rejoint", value=discord.utils.format_dt(membre.joined_at, 'D'), inline=True)
        embed.add_field(name="🎭 Rôles", value=", ".join([r.mention for r in membre.roles[1:][:15]]) or "Aucun", inline=False)
        embed.add_field(name="🔑 Permissions", value=", ".join([p[0].replace('_', ' ').title() for p in membre.guild_permissions if p[1]][:10]) or "Aucune", inline=False)
        if membre.premium_since:
            embed.add_field(name="🚀 Nitro Boost", value=discord.utils.format_dt(membre.premium_since, 'R'), inline=True)
        status_emoji = {"online": "🟢", "idle": "🟡", "dnd": "🔴", "offline": "⚫"}
        embed.add_field(name="📊 Statut", value=f"{status_emoji.get(str(membre.status), '❓')} {str(membre.status).title()}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Afficher l'avatar d'un membre")
    @app_commands.describe(membre="Le membre")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {membre.name}", color=membre.color)
        embed.set_image(url=membre.display_avatar.url)
        embed.add_field(name="PNG", value=f"[Lien]({membre.display_avatar.with_format('png')})", inline=True)
        embed.add_field(name="JPG", value=f"[Lien]({membre.display_avatar.with_format('jpg')})", inline=True)
        embed.add_field(name="WEBP", value=f"[Lien]({membre.display_avatar.with_format('webp')})", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Afficher la bannière d'un membre")
    @app_commands.describe(membre="Le membre")
    async def banner(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        user = await self.bot.fetch_user(membre.id)
        if user.banner:
            embed = discord.Embed(title=f"🖼️ Bannière de {membre.name}", color=membre.color)
            embed.set_image(url=user.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ {membre.name} n'a pas de bannière.", ephemeral=True)

    @app_commands.command(name="membercount", description="Nombre de membres du serveur")
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"👥 Membres de {guild.name}", color=0x5865F2)
        embed.add_field(name="Total", value=str(guild.member_count))
        embed.add_field(name="Humains", value=str(sum(1 for m in guild.members if not m.bot)))
        embed.add_field(name="Bots", value=str(sum(1 for m in guild.members if m.bot)))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="servericon", description="Afficher l'icône du serveur")
    async def servericon(self, interaction: discord.Interaction):
        if interaction.guild.icon:
            embed = discord.Embed(title=f"🖼️ Icône de {interaction.guild.name}", color=0x5865F2)
            embed.set_image(url=interaction.guild.icon.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Ce serveur n'a pas d'icône.", ephemeral=True)

    @app_commands.command(name="ping", description="Afficher la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏓 Pong!", color=0x57F287)
        embed.add_field(name="Latence", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="API", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uptime", description="Temps d'activité du bot")
    async def uptime(self, interaction: discord.Interaction):
        uptime = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed = discord.Embed(title="⏱️ Uptime", color=0x5865F2)
        embed.add_field(name="Temps", value=f"{days}j {hours}h {minutes}m {seconds}s")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Informations sur le bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Informations Bot", color=0x5865F2)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Nom", value=str(self.bot.user), inline=True)
        embed.add_field(name="ID", value=str(self.bot.user.id), inline=True)
        embed.add_field(name="Serveurs", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Utilisateurs", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="RAM", value=f"{psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.1f} MB", inline=True)
        embed.add_field(name="Uptime", value=str(datetime.utcnow() - self.bot.start_time).split('.')[0], inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roleinfo", description="Informations sur un rôle")
    @app_commands.describe(role="Le rôle à inspecter")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=f"🎭 {role.name}", color=role.color)
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.add_field(name="Couleur", value=str(role.color), inline=True)
        embed.add_field(name="Membres", value=str(len(role.members)), inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Mentionnable", value="✅" if role.mentionable else "❌", inline=True)
        embed.add_field(name="Affiché séparément", value="✅" if role.hoist else "❌", inline=True)
        embed.add_field(name="Créé le", value=discord.utils.format_dt(role.created_at, 'D'), inline=True)
        perms = [p[0].replace('_', ' ').title() for p in role.permissions if p[1]]
        if perms:
            embed.add_field(name="Permissions", value=", ".join(perms[:20]), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="Informations sur un salon")
    @app_commands.describe(channel="Le salon à inspecter")
    async def channelinfo(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel = None):
        channel = channel or interaction.channel
        embed = discord.Embed(title=f"📢 {channel.name}", color=0x5865F2)
        embed.add_field(name="ID", value=str(channel.id), inline=True)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
        embed.add_field(name="Créé le", value=discord.utils.format_dt(channel.created_at, 'D'), inline=True)
        embed.add_field(name="Catégorie", value=str(channel.category) if channel.category else "Aucune", inline=True)
        if isinstance(channel, discord.TextChannel):
            embed.add_field(name="NSFW", value="✅" if channel.is_nsfw() else "❌", inline=True)
            embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s", inline=True)
            topic = channel.topic or "Aucun"
            embed.add_field(name="Topic", value=topic[:1024], inline=False)
        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(name="Limite", value=str(channel.user_limit) or "Illimité", inline=True)
            embed.add_field(name="Bitrate", value=f"{channel.bitrate // 1000}kbps", inline=True)
            embed.add_field(name="Connecté", value=str(len(channel.members)), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roles", description="Liste des rôles du serveur")
    async def roles(self, interaction: discord.Interaction):
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        role_list = "\n".join([f"{r.mention} ({len(r.members)} membres)" for r in roles[:30]])
        embed = discord.Embed(title=f"🎭 Rôles ({len(roles)})", description=role_list, color=0x5865F2)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="boosts", description="Nombre de boosts du serveur")
    async def boosts(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title="🚀 Boosts", color=0xF47FFF)
        embed.add_field(name="Nombre de boosts", value=str(guild.premium_subscription_count))
        embed.add_field(name="Niveau", value=str(guild.premium_tier))
        if guild.premium_subscribers:
            boosters = ", ".join([b.mention for b in guild.premium_subscribers[:20]])
            embed.add_field(name="Boosters", value=boosters, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="id", description="Afficher l'ID d'un membre ou du serveur")
    @app_commands.describe(membre="Le membre")
    async def getid(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title="🆔 ID", color=0x5865F2)
        embed.add_field(name="Membre", value=str(membre.id))
        embed.add_field(name="Serveur", value=str(interaction.guild.id))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invitecount", description="Nombre d'invitations d'un membre")
    @app_commands.describe(membre="Le membre")
    async def invitecount(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        total = 0
        for channel in interaction.guild.text_channels:
            try:
                invites = await channel.invites()
                for inv in invites:
                    if inv.inviter == membre:
                        total += inv.uses
            except:
                pass
        await interaction.response.send_message(f"📨 {membre.mention} a **{total}** invitations.")

    @app_commands.command(name="poll", description="Créer un sondage")
    @app_commands.describe(question="La question du sondage", options="Options séparées par ; (max 10)")
    async def poll(self, interaction: discord.Interaction, question: str, options: str = ""):
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        embed = discord.Embed(title=f"📊 {question}", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_footer(text=f"Créé par {interaction.user}")
        if options:
            option_list = [o.strip() for o in options.split(";") if o.strip()]
            if len(option_list) < 2 or len(option_list) > 10:
                return await interaction.response.send_message("❌ Entre 2 et 10 options requises.", ephemeral=True)
            desc = "\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(option_list)])
            embed.description = desc
            msg = await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            for i in range(len(option_list)):
                await msg.add_reaction(emojis[i])
        else:
            embed.description = "✅ Oui\n❌ Non"
            msg = await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

    @app_commands.command(name="say", description="Faire dire un message au bot")
    @app_commands.describe(message="Le message")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

    @app_commands.command(name="remindme", description="Rappel personnel")
    @app_commands.describe(duree="Durée en minutes", message="Message de rappel")
    async def remindme(self, interaction: discord.Interaction, duree: int, message: str):
        await interaction.response.send_message(f"⏰ Rappel créé pour **{duree}** minutes: {message}")
        await asyncio.sleep(duree * 60)
        try:
            await interaction.user.send(f"⏰ **Rappel:** {message}")
        except:
            pass

    @app_commands.command(name="afk", description="Se mettre AFK")
    @app_commands.describe(reason="Raison de l'AFK")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        try:
            await interaction.user.edit(nick=f"[AFK] {interaction.user.display_name[:15]}")
        except:
            pass
        embed = discord.Embed(title="💤 AFK activé", description=f"{interaction.user.mention} est AFK: {reason}", color=0xFEE75C)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="steal", description="Voler un emoji du serveur")
    @app_commands.describe(emoji="L'emoji à voler", nom="Nom du nouvel emoji")
    @app_commands.checks.has_permissions(manage_emojis=True)
    async def steal(self, interaction: discord.Interaction, emoji: str, nom: str = ""):
        if not emoji:
            return await interaction.response.send_message("❌ Fournis un emoji.", ephemeral=True)
        if emoji.startswith("<"):
            animated = emoji.startswith("<a:")
            name = nom or emoji.split(":")[1]
            emoji_id = emoji.split(":")[2].replace(">", "")
            url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"
        else:
            return await interaction.response.send_message("❌ Emoji custom requis.", ephemeral=True)
        async with self.bot.http._HTTPClient__session.get(url) as resp:
            if resp.status != 200:
                return await interaction.response.send_message("❌ Impossible de télécharger l'emoji.", ephemeral=True)
            data = await resp.read()
        new_emoji = await interaction.guild.create_custom_emoji(name=name, image=data)
        await interaction.response.send_message(f"✅ Emoji {new_emoji} créé!")

    @app_commands.command(name="emotes", description="Liste des emojis du serveur")
    async def emotes(self, interaction: discord.Interaction):
        emojis = interaction.guild.emojis
        if not emojis:
            return await interaction.response.send_message("❌ Aucun emoji sur ce serveur.", ephemeral=True)
        desc = "\n".join([str(e) for e in emojis[:50]])
        embed = discord.Embed(title=f"😀 Emojis ({len(emojis)})", description=desc, color=0x5865F2)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="calculate", description="Calculer une expression mathématique")
    @app_commands.describe(expression="L'expression à calculer")
    async def calculate(self, interaction: discord.Interaction, expression: str):
        try:
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return await interaction.response.send_message("❌ Caractères non autorisés.", ephemeral=True)
            result = eval(expression)
            embed = discord.Embed(title="🧮 Calcul", color=0x5865F2)
            embed.add_field(name="Expression", value=f"`{expression}`", inline=False)
            embed.add_field(name="Résultat", value=f"`{result}`", inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
