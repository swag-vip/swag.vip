import discord
from discord.ext import commands
from discord import app_commands
import random

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addrole", description="Ajouter un rôle à un membre")
    @app_commands.describe(membre="Le membre", role="Le rôle à ajouter")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def addrole(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal au tien.", ephemeral=True)
        if role in membre.roles:
            return await interaction.response.send_message(f"❌ {membre.mention} a déjà ce rôle.", ephemeral=True)
        await membre.add_roles(role, reason=f"Ajouté par {interaction.user}")
        await interaction.response.send_message(f"✅ Rôle **{role.name}** ajouté à {membre.mention}.")

    @app_commands.command(name="removerole", description="Retirer un rôle à un membre")
    @app_commands.describe(membre="Le membre", role="Le rôle à retirer")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def removerole(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal au tien.", ephemeral=True)
        if role not in membre.roles:
            return await interaction.response.send_message(f"❌ {membre.mention} n'a pas ce rôle.", ephemeral=True)
        await membre.remove_roles(role, reason=f"Retiré par {interaction.user}")
        await interaction.response.send_message(f"✅ Rôle **{role.name}** retiré à {membre.mention}.")

    @app_commands.command(name="createrole", description="Créer un rôle")
    @app_commands.describe(name="Nom du rôle", color="Couleur hex", permissions="Permissions séparées par ;")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def createrole(self, interaction: discord.Interaction, name: str, color: str = "#000000", permissions: str = ""):
        try:
            role_color = discord.Color(int(color.replace("#", ""), 16))
        except:
            role_color = discord.Color.default()
        perms = discord.Permissions()
        if permissions:
            for p in permissions.split(";"):
                p = p.strip().lower().replace(" ", "_")
                if hasattr(perms, p):
                    setattr(perms, p, True)
        role = await interaction.guild.create_role(name=name, color=role_color, permissions=perms)
        await interaction.response.send_message(f"✅ Rôle **{role.mention}** créé!")

    @app_commands.command(name="deleterole", description="Supprimer un rôle")
    @app_commands.describe(role="Le rôle à supprimer")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def deleterole(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal au tien.", ephemeral=True)
        name = role.name
        await role.delete()
        await interaction.response.send_message(f"✅ Rôle **{name}** supprimé.")

    @app_commands.command(name="editrole", description="Modifier un rôle")
    @app_commands.describe(role="Le rôle", name="Nouveau nom", color="Nouvelle couleur hex")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def editrole(self, interaction: discord.Interaction, role: discord.Role, name: str = None, color: str = None):
        kwargs = {}
        if name:
            kwargs["name"] = name
        if color:
            try:
                kwargs["color"] = discord.Color(int(color.replace("#", ""), 16))
            except:
                return await interaction.response.send_message("❌ Couleur hex invalide.", ephemeral=True)
        if kwargs:
            await role.edit(**kwargs)
        await interaction.response.send_message(f"✅ Rôle **{role.name}** mis à jour.")

    @app_commands.command(name="roleall", description="Donner un rôle à tous les membres")
    @app_commands.describe(role="Le rôle à donner")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roleall(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Ce rôle est supérieur ou égal au tien.", ephemeral=True)
        await interaction.response.defer()
        count = 0
        for member in interaction.guild.members:
            if role not in member.roles and not member.bot:
                try:
                    await member.add_roles(role, reason=f"Role all par {interaction.user}")
                    count += 1
                except:
                    pass
        await interaction.followup.send(f"✅ Rôle **{role.name}** donné à **{count}** membres.")

    @app_commands.command(name="rolemembers", description="Voir les membres d'un rôle")
    @app_commands.describe(role="Le rôle")
    async def rolemembers(self, interaction: discord.Interaction, role: discord.Role):
        members = role.members
        if not members:
            return await interaction.response.send_message(f"❌ Aucun membre avec le rôle **{role.name}**.", ephemeral=True)
        desc = "\n".join([f"• {m.mention}" for m in members[:30]])
        if len(members) > 30:
            desc += f"\n... et {len(members) - 30} autres"
        embed = discord.Embed(title=f"🎭 Membres avec {role.name} ({len(members)})", description=desc, color=role.color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="color", description="Changer la couleur d'un rôle")
    @app_commands.describe(role="Le rôle", hex_color="Couleur hex (ex: #FF0000)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def color(self, interaction: discord.Interaction, role: discord.Role, hex_color: str):
        try:
            new_color = discord.Color(int(hex_color.replace("#", ""), 16))
        except:
            return await interaction.response.send_message("❌ Couleur hex invalide.", ephemeral=True)
        await role.edit(color=new_color)
        await interaction.response.send_message(f"✅ Couleur de **{role.name}** changée en {hex_color}")

    @app_commands.command(name="hoist", description="Activer/Désactiver l'affichage séparé d'un rôle")
    @app_commands.describe(role="Le rôle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def hoist(self, interaction: discord.Interaction, role: discord.Role):
        await role.edit(hoist=not role.hoist)
        state = "activé" if role.hoist else "désactivé"
        await interaction.response.send_message(f"✅ Affichage séparé {state} pour **{role.name}**.")

    @app_commands.command(name="mentionable", description="Rendre un rôle mentionnable ou non")
    @app_commands.describe(role="Le rôle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def mentionable(self, interaction: discord.Interaction, role: discord.Role):
        await role.edit(mentionable=not role.mentionable)
        state = "mentionnable" if role.mentionable else "non mentionnable"
        await interaction.response.send_message(f"✅ **{role.name}** est maintenant {state}.")

    @app_commands.command(name="allroles", description="Liste de tous les rôles")
    async def allroles(self, interaction: discord.Interaction):
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        desc = "\n".join([f"{r.mention} — {len(r.members)} membres — Position {r.position}" for r in roles[:30]])
        embed = discord.Embed(title=f"🎭 Tous les rôles ({len(roles)})", description=desc, color=0x5865F2)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="positions", description="Afficher les positions des rôles")
    async def positions(self, interaction: discord.Interaction):
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        desc = "\n".join([f"**{r.position}** — {r.mention}" for r in roles[:30]])
        embed = discord.Embed(title="📍 Positions des rôles", description=desc, color=0x5865F2)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))
