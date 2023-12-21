import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import threading
import random
import asyncio
import time

class Mod(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.lock = threading.Lock()

  def get_modset(self, guild_id):
    return f'data/mod_{guild_id}.txt'

  def load_modlog(self, guild_id):
    with self.lock:
      path = self.get_log(guild_id)
      if not os.path.exists(path):
        return None
      with open(path, "r") as file:
        data = json.load(file)
        return int(data.get("mod_log_channel"))

  def save_modlog(self, guild_id, channel_id):
    with self.lock:
      path = self.get_log(guild_id)
      data = {'mod_log_channel': channel_id}
      with open(path, "w") as file:
        json.dump(data, file, indent=4)

  async def log_to_channel(self, channel_id, action, mod_user, eff_user, reason):
    channel = self.bot.get_channel(channel_id)
    if channel is None:
      print(f"Failed to find channel with ID: {channel_id}")
      return

    embed = discord.Embed(
        title=f'User {action}',
        color=0xBF713D
    )
    embed.add_field(name="Effected User", value='\n'f'{eff_user}', inline=False)
    if user_ident:
      embed.add_field(name = "Perpetrator:", value = '\n'f'{mod_user}', inline = False)
      if reason:
        embed.add_field(name = 'Reason:', value = '\n'f'{reason}', inline = False)


    await channel.send(embed=embed)

  @app_commands.command(name = 'kick', description = 'Kick a member')
  @app_commands.guild_only()
  @app_commands.has_permissions(kick_members = True)
  async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
    if member.id == interaction.member.id:
      embed = discord.Embed(
        title = "We can't let this happen!",
        description = f"Sorry {interaction.user.name}, but you can't kick yourself!",
        color = 0xBF713D
      )
      await interaction.response.send_message(embed = embed, ephemeral = True)

    if not interaction.user.guild_permissions.kick_members:
      embed = discord.Embed(
        title = "Danger Danger Will Robinson",
        description = "You appear to be missing the `kick_members` permissions"
        color = 0xBF713D
      )
      await interaction.response.send_message(embed = embed, ephemeral = True)
    member.kick(reason = reason)
    log_channel_id = self.load_log(guild_id: interaction.guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)
  
