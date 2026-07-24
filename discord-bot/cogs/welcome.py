import discord
from discord.ext import commands
from discord import app_commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setwelcome", description="Configurer le message de bienvenue")
    @app_commands.describe(
        channel="Le salon de bienvenue",
        message="Message (utilise {user}, {server}, {members}, {member_count})"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "welcome_channel", str(channel.id))
        )
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "welcome_message", message)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Message de bienvenue configuré dans {channel.mention}")

    @app_commands.command(name="setgoodbye", description="Configurer le message d'au revoir")
    @app_commands.describe(
        channel="Le salon d'au revoir",
        message="Message (utilise {user}, {server}, {members})"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setgoodbye(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "goodbye_channel", str(channel.id))
        )
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "goodbye_message", message)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Message d'au revoir configuré dans {channel.mention}")

    @app_commands.command(name="setwelcome-embed", description="Configurer l'embed de bienvenue")
    @app_commands.describe(
        title="Titre de l'embed",
        color="Couleur hex",
        image="URL de l'image",
        thumbnail="URL de la miniature"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome_embed(
        self, interaction: discord.Interaction,
        title: str = "Bienvenue!",
        color: str = "#5865F2",
        image: str = "",
        thumbnail: str = ""
    ):
        settings = f"{title}|{color}|{image}|{thumbnail}"
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "welcome_embed", settings)
        )
        await self.bot.db.commit()
        await interaction.response.send_message("✅ Embed de bienvenue configuré!")

    @app_commands.command(name="autorole", description="Attribuer un rôle automatiquement aux nouveaux membres")
    @app_commands.describe(role="Le rôle à donner automatiquement")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur à celui du bot.", ephemeral=True)
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "autorole", str(role.id))
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Auto-rôle configuré: {role.mention}")

    @app_commands.command(name="testwelcome", description="Tester le message de bienvenue")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def testwelcome(self, interaction: discord.Interaction):
        channel_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'welcome_channel'",
            (interaction.guild.id,)
        )
        ch_row = await channel_cursor.fetchone()
        if not ch_row:
            return await interaction.response.send_message("❌ Salon de bienvenue non configuré.", ephemeral=True)
        channel = interaction.guild.get_channel(int(ch_row[0]))
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        await self.send_welcome(interaction.guild, interaction.user)
        await interaction.response.send_message(f"✅ Message de bienvenue testé dans {channel.mention}", ephemeral=True)

    async def send_welcome(self, guild, member):
        ch_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'welcome_channel'",
            (guild.id,)
        )
        ch_row = await ch_cursor.fetchone()
        if not ch_row:
            return
        channel = guild.get_channel(int(ch_row[0]))
        if not channel:
            return

        msg_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'welcome_message'",
            (guild.id,)
        )
        msg_row = await msg_cursor.fetchone()
        message = msg_row[0] if msg_row else "Bienvenue {user} sur **{server}**!"

        message = message.replace("{user}", member.mention)
        message = message.replace("{server}", guild.name)
        message = message.replace("{members}", str(guild.member_count))
        message = message.replace("{member_count}", str(guild.member_count))

        embed_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'welcome_embed'",
            (guild.id,)
        )
        embed_row = await embed_cursor.fetchone()

        if embed_row:
            parts = embed_row[0].split("|")
            title = parts[0] if parts else "Bienvenue!"
            color = int(parts[1].replace("#", ""), 16) if len(parts) > 1 and parts[1] else 0x5865F2
            image = parts[2] if len(parts) > 2 else ""
            thumbnail = parts[3] if len(parts) > 3 else ""

            embed = discord.Embed(title=title, description=message, color=color)
            embed.set_thumbnail(url=member.display_avatar.url)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            if image:
                embed.set_image(url=image)
            embed.set_footer(text=f"Membre #{guild.member_count}")
            await channel.send(embed=embed)
        else:
            await channel.send(message)

    async def send_goodbye(self, guild, member):
        ch_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'goodbye_channel'",
            (guild.id,)
        )
        ch_row = await ch_cursor.fetchone()
        if not ch_row:
            return
        channel = guild.get_channel(int(ch_row[0]))
        if not channel:
            return

        msg_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'goodbye_message'",
            (guild.id,)
        )
        msg_row = await msg_cursor.fetchone()
        message = msg_row[0] if msg_row else "Au revoir **{user}**! Tu vas nous manquer!"

        message = message.replace("{user}", str(member))
        message = message.replace("{server}", guild.name)
        message = message.replace("{members}", str(guild.member_count))

        await channel.send(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_welcome(member.guild, member)
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'autorole'",
            (member.guild.id,)
        )
        row = await cursor.fetchone()
        if row:
            role = member.guild.get_role(int(row[0]))
            if role:
                try:
                    await member.add_roles(role, reason="Auto-rôle")
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_goodbye(member.guild, member)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
