import discord
from discord.ext import commands
from discord import app_commands
import json
import re

class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Créer un embed personnalisé")
    @app_commands.describe(
        titre="Titre de l'embed",
        description="Description de l'embed",
        color="Couleur hex (ex: #5865F2)",
        image="URL de l'image",
        thumbnail="URL de la miniature",
        footer="Texte de pied",
        author="Nom de l'auteur"
    )
    async def embed(
        self, interaction: discord.Interaction,
        titre: str,
        description: str = "",
        color: str = "#5865F2",
        image: str = "",
        thumbnail: str = "",
        footer: str = "",
        author: str = ""
    ):
        try:
            embed_color = int(color.replace("#", ""), 16)
        except:
            embed_color = 0x5865F2

        em = discord.Embed(title=titre, description=description, color=embed_color)
        if image:
            em.set_image(url=image)
        if thumbnail:
            em.set_thumbnail(url=thumbnail)
        if footer:
            em.set_footer(text=footer)
        if author:
            em.set_author(name=author)

        await interaction.response.send_message(embed=em)

    @app_commands.command(name="announce", description="Envoyer une announcement")
    @app_commands.describe(
        channel="Le salon d'envoi",
        titre="Titre",
        message="Message",
        color="Couleur hex",
        ping="Rôle à ping"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announce(
        self, interaction: discord.Interaction,
        channel: discord.TextChannel,
        titre: str,
        message: str,
        color: str = "#5865F2",
        ping: discord.Role = None
    ):
        try:
            embed_color = int(color.replace("#", ""), 16)
        except:
            embed_color = 0x5865F2

        embed = discord.Embed(title=f"📢 {titre}", description=message, color=embed_color)
        embed.set_footer(text=f"Annoncé par {interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        ping_text = ping.mention if ping else ""
        await channel.send(content=ping_text, embed=embed)
        await interaction.response.send_message(f"✅ Annonce envoyée dans {channel.mention}", ephemeral=True)

    @app_commands.command(name="sayembed", description="Faire dire un message embed au bot")
    @app_commands.describe(channel="Le salon", titre="Titre", message="Description", color="Couleur hex")
    async def sayembed(
        self, interaction: discord.Interaction,
        channel: discord.TextChannel,
        titre: str,
        message: str,
        color: str = "#5865F2"
    ):
        try:
            embed_color = int(color.replace("#", ""), 16)
        except:
            embed_color = 0x5865F2
        em = discord.Embed(title=titre, description=message, color=embed_color)
        await channel.send(embed=em)
        await interaction.response.send_message(f"✅ Embed envoyé dans {channel.mention}", ephemeral=True)

    @app_commands.command(name="poll-embed", description="Créer un poll avec embed")
    @app_commands.describe(question="La question", options="Options séparées par ;")
    async def poll_embed(self, interaction: discord.Interaction, question: str, options: str):
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        option_list = [o.strip() for o in options.split(";") if o.strip()]
        if len(option_list) < 2 or len(option_list) > 10:
            return await interaction.response.send_message("❌ Entre 2 et 10 options.", ephemeral=True)

        desc = "\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(option_list)])
        embed = discord.Embed(title=f"📊 {question}", description=desc, color=0x5865F2)
        embed.set_footer(text=f"Sondage par {interaction.user}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(option_list)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="serverrules", description="Afficher les règles du serveur")
    @app_commands.describe(rules="Règles séparées par ;")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def serverrules(self, interaction: discord.Interaction, rules: str):
        rule_list = rules.split(";")
        desc = ""
        for i, rule in enumerate(rule_list, 1):
            desc += f"**{i}.** {rule.strip()}\n"
        embed = discord.Embed(title="📜 Règles du Serveur", description=desc, color=0xED4245)
        embed.set_footer(text=f"{interaction.guild.name} • Règles officielles")
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embededit", description="Modifier l'embed dans un salon")
    @app_commands.describe(channel="Le salon", message_id="ID du message embed", titre="Nouveau titre", description="Nouvelle description")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embededit(
        self, interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_id: str,
        titre: str = None,
        description: str = None
    ):
        try:
            message = await channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
        if not message.embeds:
            return await interaction.response.send_message("❌ Ce message n'est pas un embed.", ephemeral=True)
        embed = message.embeds[0]
        if titre:
            embed.title = titre
        if description:
            embed.description = description
        await message.edit(embed=embed)
        await interaction.response.send_message("✅ Embed modifié!", ephemeral=True)

    @app_commands.command(name="template-embed", description="Templates d'embeds prédéfinis")
    @app_commands.describe(template="Le template", channel="Le salon d'envoi")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def template_embed(self, interaction: discord.Interaction, template: str, channel: discord.TextChannel):
        templates = {
            "rules": {
                "title": "📜 Règles du Serveur",
                "description": "1. Respecter tous les membres\n2. Pas de spam\n3. Pas de contenu NSFW\n4. Pas de publicité non autorisée\n5. Utiliser les salons appropriés",
                "color": 0xED4245
            },
            "welcome": {
                "title": "👋 Bienvenue!",
                "description": "Bienvenue sur le serveur! Lis les règles et amuse-toi bien!",
                "color": 0x57F287
            },
            "roles": {
                "title": "🎭 Choisis tes rôles!",
                "description": "Clique sur les réactions pour obtenir tes rôles!",
                "color": 0x5865F2
            },
            "info": {
                "title": "ℹ️ Informations",
                "description": "Retrouve toutes les infos ici!",
                "color": 0x5865F2
            },
            "faq": {
                "title": "❓ Questions Fréquentes",
                "description": "**Q: Comment rejoindre vocal?**\nR: Va dans un salon vocal!\n\n**Q: Où trouver le staff?**\nR: Tape /staff",
                "color": 0xFEE75C
            },
            "rules-fr": {
                "title": "📜 Règlement",
                "description": "**1.** Respect mutuel\n**2.** Pas de harcèlement\n**3.** Pas de spam/flood\n**4.** Contenu approprié uniquement\n**5.** Écouter le staff\n**6.** Pas de/publicité sauf salon dédié\n**7.** Utiliser le bon salon\n**8.** Pas de giveaway gratuit\n**9.** Pas de NSFW\n**10.** Amusez-vous!",
                "color": 0xED4245
            },
            "giveaway": {
                "title": "🎉 GIVEAWAY",
                "description": "Réagis avec 🎉 pour participer!\nRécompense à gagner!\n\nBonne chance à tous!",
                "color": 0xFFD700
            },
            "ticket-info": {
                "title": "🎫 Support",
                "description": "Besoin d'aide? Ouvre un ticket!\nClique sur le bouton ci-dessous.",
                "color": 0x57F287
            }
        }

        if template.lower() not in templates:
            t_list = "\n".join([f"• `{t}`" for t in templates.keys()])
            return await interaction.response.send_message(f"❌ Templates disponibles:\n{t_list}", ephemeral=True)

        t = templates[template.lower()]
        embed = discord.Embed(title=t["title"], description=t["description"], color=t["color"])
        embed.set_footer(text=interaction.guild.name)
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Template `{template}` envoyé dans {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Embeds(bot))
