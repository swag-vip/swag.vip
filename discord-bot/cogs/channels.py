import discord
from discord.ext import commands
from discord import app_commands

class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createchannel", description="Créer un salon")
    @app_commands.describe(name="Nom du salon", type="Type (texte/voice)", category="Catégorie parente")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def createchannel(self, interaction: discord.Interaction, name: str, type: str = "texte", category: discord.CategoryChannel = None):
        if type.lower() == "texte":
            ch = await interaction.guild.create_text_channel(name, category=category)
        elif type.lower() == "voice":
            ch = await interaction.guild.create_voice_channel(name, category=category)
        else:
            return await interaction.response.send_message("❌ Type: 'texte' ou 'voice'.", ephemeral=True)
        await interaction.response.send_message(f"✅ Salon {ch.mention} créé!")

    @app_commands.command(name="deletechannel", description="Supprimer un salon")
    @app_commands.describe(channel="Le salon à supprimer")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def deletechannel(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        if channel == interaction.channel:
            return await interaction.response.send_message("❌ Tu ne peux pas supprimer ce salon ici.", ephemeral=True)
        name = channel.name
        await channel.delete()
        await interaction.response.send_message(f"✅ Salon `{name}` supprimé.")

    @app_commands.command(name="renamechannel", description="Renommer un salon")
    @app_commands.describe(channel="Le salon", name="Nouveau nom")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def renamechannel(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel, name: str):
        old = channel.name
        await channel.edit(name=name)
        await interaction.response.send_message(f"✅ Salon renommé: `{old}` → `{name}`")

    @app_commands.command(name="clone", description="Cloner un salon")
    @app_commands.describe(channel="Le salon à cloner")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def clone(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        new = await channel.clone(reason=f"Cloné par {interaction.user}")
        await interaction.response.send_message(f"✅ Salon cloné: {new.mention}")

    @app_commands.command(name="nsfw", description="Basculer le NSFW d'un salon")
    @app_commands.describe(channel="Le salon")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nsfw(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await channel.edit(nsfw=not channel.is_nsfw())
        state = "activé" if channel.is_nsfw() else "désactivé"
        await interaction.response.send_message(f"✅ NSFW {state} pour {channel.mention}")

    @app_commands.command(name="topic", description="Changer le topic d'un salon")
    @app_commands.describe(channel="Le salon", topic="Nouveau topic")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def topic(self, interaction: discord.Interaction, channel: discord.TextChannel, topic: str):
        await channel.edit(topic=topic[:1024])
        await interaction.response.send_message(f"✅ Topic de {channel.mention} mis à jour.")

    @app_commands.command(name="category", description="Créer une catégorie")
    @app_commands.describe(name="Nom de la catégorie")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def category(self, interaction: discord.Interaction, name: str):
        cat = await interaction.guild.create_category(name)
        await interaction.response.send_message(f"✅ Catégorie **{cat.name}** créée!")

    @app_commands.command(name="setposition", description="Changer la position d'un salon")
    @app_commands.describe(channel="Le salon", position="Nouvelle position")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setposition(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel, position: int):
        await channel.edit(position=position)
        await interaction.response.send_message(f"✅ Position de {channel.mention} changée à **{position}**.")

    @app_commands.command(name="sync", description="Synchroniser les permissions d'un salon avec sa catégorie")
    @app_commands.describe(channel="Le salon")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def sync(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        if channel.category:
            await channel.edit(sync_permissions=True)
            await interaction.response.send_message(f"✅ Permissions de {channel.mention} synchronisées avec la catégorie.")
        else:
            await interaction.response.send_message("❌ Ce salon n'a pas de catégorie.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))
