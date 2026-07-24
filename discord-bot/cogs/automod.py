import discord
from discord.ext import commands
from discord import app_commands
import re
from collections import defaultdict
from datetime import datetime, timedelta

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = defaultdict(list)
        self.antispam_config = {}
        self.antilink_config = {}
        self.wordfilter_config = {}

    async def get_config(self, guild_id, key):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = ?",
            (guild_id, key)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    @app_commands.command(name="automod-setup", description="Configurer l'auto-modération")
    @app_commands.describe(
        antispam="Activer l'anti-spam (messages/seconde)",
        antilink="Activer l'anti-liens",
        wordfilter="Activer le filtre de mots"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_setup(
        self, interaction: discord.Interaction,
        antispam: bool = True,
        antilink: bool = True,
        wordfilter: bool = True
    ):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "antispam", str(antispam).lower())
        )
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "antilink", str(antilink).lower())
        )
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "wordfilter", str(wordfilter).lower())
        )
        await self.bot.db.commit()
        embed = discord.Embed(title="🤖 Auto-Mod Configuré", color=0x57F287)
        embed.add_field(name="Anti-Spam", value="✅" if antispam else "❌")
        embed.add_field(name="Anti-Links", value="✅" if antilink else "❌")
        embed.add_field(name="Word Filter", value="✅" if wordfilter else "❌")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="automod-config", description="Voir la config auto-mod")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_config(self, interaction: discord.Interaction):
        antispam = await self.get_config(interaction.guild.id, "antispam")
        antilink = await self.get_config(interaction.guild.id, "antilink")
        wordfilter = await self.get_config(interaction.guild.id, "wordfilter")
        embed = discord.Embed(title="🤖 Config Auto-Mod", color=0x5865F2)
        embed.add_field(name="Anti-Spam", value="✅" if antispam == "true" else "❌")
        embed.add_field(name="Anti-Links", value="✅" if antilink == "true" else "❌")
        embed.add_field(name="Word Filter", value="✅" if wordfilter == "true" else "❌")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="antispam-config", description="Configurer l'anti-spam")
    @app_commands.describe(messages="Messages max par fenêtre", duree="Fenêtre en secondes", action="Action (mute/kick/ban/delete)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antispam_config(self, interaction: discord.Interaction, messages: int = 5, duree: int = 10, action: str = "mute"):
        self.antispam_config[interaction.guild.id] = {"messages": messages, "duration": duree, "action": action}
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "antispam_config", f"{messages}:{duree}:{action}")
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Anti-spam: {messages} messages/{duree}s → {action}")

    @app_commands.command(name="antilink-config", description="Configurer l'anti-liens")
    @app_commands.describe(channels="Ignorer certains salons (IDs séparés par ;)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_config(self, interaction: discord.Interaction, channels: str = ""):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "antilink_channels", channels)
        )
        await self.bot.db.commit()
        await interaction.response.send_message("✅ Configuration anti-liens mise à jour.")

    @app_commands.command(name="wordfilter-add", description="Ajouter un mot au filtre")
    @app_commands.describe(mot="Le mot à filtrer")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def wordfilter_add(self, interaction: discord.Interaction, mot: str):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'wordfilter_list'",
            (interaction.guild.id,)
        )
        row = await cursor.fetchone()
        words = row[0].split(";") if row and row[0] else []
        if mot.lower() not in words:
            words.append(mot.lower())
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "wordfilter_list", ";".join(words))
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Mot `{mot}` ajouté au filtre.")

    @app_commands.command(name="wordfilter-remove", description="Retirer un mot du filtre")
    @app_commands.describe(mot="Le mot à retirer")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def wordfilter_remove(self, interaction: discord.Interaction, mot: str):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'wordfilter_list'",
            (interaction.guild.id,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            words = [w for w in row[0].split(";") if w != mot.lower()]
            await self.bot.db.execute(
                "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
                (interaction.guild.id, "wordfilter_list", ";".join(words))
            )
            await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Mot `{mot}` retiré du filtre.")

    @app_commands.command(name="wordfilter-list", description="Voir les mots filtrés")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def wordfilter_list(self, interaction: discord.Interaction):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'wordfilter_list'",
            (interaction.guild.id,)
        )
        row = await cursor.fetchone()
        words = row[0].split(";") if row and row[0] else []
        if not words:
            return await interaction.response.send_message("❌ Aucun mot filtré.", ephemeral=True)
        embed = discord.Embed(title="🚫 Mots filtrés", description="\n".join([f"`{w}`" for w in words]), color=0xED4245)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whitelist-add", description="Ajouter un salon/user à la whitelist anti-spam")
    @app_commands.describe(cible="Salon ou membre")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def whitelist_add(self, interaction: discord.Interaction, cible: str):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'antispam_whitelist'",
            (interaction.guild.id,)
        )
        row = await cursor.fetchone()
        whitelist = row[0].split(";") if row and row[0] else []
        if cible not in whitelist:
            whitelist.append(cible)
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
            (interaction.guild.id, "antispam_whitelist", ";".join(whitelist))
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ {cible} ajouté à la whitelist.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if await self.is_whitelisted(message):
            return

        antispam = await self.get_config(message.guild.id, "antispam")
        if antispam == "true":
            await self.check_spam(message)

        antilink = await self.get_config(message.guild.id, "antilink")
        if antilink == "true":
            await self.check_links(message)

        wordfilter = await self.get_config(message.guild.id, "wordfilter")
        if wordfilter == "true":
            await self.check_words(message)

    async def is_whitelisted(self, message):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'antispam_whitelist'",
            (message.guild.id,)
        )
        row = await cursor.fetchone()
        if not row or not row[0]:
            return False
        whitelist = row[0].split(";")
        if str(message.channel.id) in whitelist:
            return True
        if str(message.author.id) in whitelist:
            return True
        if message.author.guild_permissions.manage_messages:
            return True
        return False

    async def check_spam(self, message):
        config_cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'antispam_config'",
            (message.guild.id,)
        )
        config_row = await config_cursor.fetchone()
        if config_row:
            parts = config_row[0].split(":")
            max_messages = int(parts[0])
            window = int(parts[1])
            action = parts[2]
        else:
            max_messages = 5
            window = 10
            action = "mute"

        now = datetime.utcnow()
        self.spam_tracker[message.author.id].append(now)
        self.spam_tracker[message.author.id] = [
            t for t in self.spam_tracker[message.author.id]
            if (now - t).total_seconds() < window
        ]
        if len(self.spam_tracker[message.author.id]) > max_messages:
            try:
                await message.delete()
            except:
                pass
            if action == "mute":
                from datetime import timedelta
                await message.author.timeout(timedelta(seconds=300), reason="Anti-spam")
                await message.channel.send(f"🔇 {message.author.mention} mute pour spam.", delete_after=5)
            elif action == "kick":
                await message.author.kick(reason="Anti-spam")
                await message.channel.send(f"🚪 {message.author.mention} expulsé pour spam.", delete_after=5)
            elif action == "ban":
                await message.author.ban(reason="Anti-spam")
                await message.channel.send(f"🔨 {message.author.mention} banni pour spam.", delete_after=5)
            else:
                pass
            self.spam_tracker[message.author.id] = []

    async def check_links(self, message):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'antilink_channels'",
            (message.guild.id,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            ignored = row[0].split(";")
            if str(message.channel.id) in ignored:
                return
        url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
            re.IGNORECASE
        )
        if url_pattern.search(message.content):
            if not message.author.guild_permissions.manage_messages:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"🚫 {message.author.mention} Les liens ne sont pas autorisés!",
                        delete_after=5
                    )
                except:
                    pass

    async def check_words(self, message):
        cursor = await self.bot.db.execute(
            "SELECT value FROM config WHERE guild_id = ? AND key = 'wordfilter_list'",
            (message.guild.id,)
        )
        row = await cursor.fetchone()
        if not row or not row[0]:
            return
        words = row[0].split(";")
        for word in words:
            if word.lower() in message.content.lower():
                if not message.author.guild_permissions.manage_messages:
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"🚫 {message.author.mention} Mot interdit détecté!",
                            delete_after=5
                        )
                    except:
                        pass
                    break

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
