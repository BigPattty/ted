import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import threading
import random
import asyncio
import time
import brawlstats

class Brawlv2(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.locking = threading.Lock()
    self.bs = brawlstats.Client("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjVkMTI0M2VkLWI2NGMtNDY5Mi1iNjNhLTJjMzBiMjUyYjdmYSIsImlhdCI6MTcwMDIyMDA0OCwic3ViIjoiZGV2ZWxvcGVyLzg4NmY0MjNkLTJiMTEtMDU4NS01YWMyLWFhOGJmYTczMGMwZiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTMyLjE0NS42OC4xMzUiXSwidHlwZSI6ImNsaWVudCJ9XX0.TTmG5orF9i-iU7A-m1kHCJtXwVP-ddWxUTtaNLKQ_VaRVqo1kQt4Xn8x4uBTXI6lOYm_AuOhBZYVvCpqFct_-w")

  def get_player_tags(self, guild_id):
    return f'data/tags_{guild_id}.txt'

  def load_tag(self, guild_id):
    with self.lock:
        path = self.get_player_tags(guild_id)
        if not os.path.exists(path):
            with open(path, "w") as file:
                json.dump({}, file)
            return {}
        with open(path, "r") as file:
            return json.load(file)

  def save_tag(self, guild_id, user_id, tag):
    with self.lock:
        path = self.get_player_tags(guild_id)
        tags = self.load_tag(guild_id)
        tags[str(user_id)] = tag
        with open(path, 'w') as file:
            json.dump(tag, file, indent=4)

  @app_commands.command(name = 'save', description = 'Save your Brawl Stars player tag!')
  @app_commands.describe(tag='In format of #TAG123')
  async def save(self, interaction: discord.Interaction, tag: str):
    await interaction.response.defer()
    await asyncio.sleep(5)
    try:
      player = self.bs.get_player(tag)
      guild_id = interaction.guild_id
      user_id = interaction.user.id
      self.save_tag(guild_id, user_id, tag)

      embed = discord.Embed(
        title = 'What can I say except, your welcome!',
        description = f'**{tag}** has been saved to {interaction.user.name} without any issues!',
        color = 0xBF713D
      )
    except brawlstats.NotFoundError:
      embed = discord.Embed(
        title = 'Houston, we have a problem!',
        description = f'Unfortunately, the provided tag **{tag}** is not valid. Please try again!',
        color = 0xBF713D
      )
      print(f'Invalid tag: {tag} from user {interaction.user.name}')
      await interaction.followup.send(embed = embed, ephemeral = True)
    except brawlstats.RequestError as e:
      embed = discord.Embed(
        title = 'Houston, we have a problem!',
        description = 'Unfortunately, I am unable to process your request at this time! Please try again later!',
        color = 0xBF713D
      )
      print(f'The following issues occured when saving {tag} to {interaction.user.name}: {e}')
      await interaction.response.send(embed = embed, ephemeral = True)

  @app_commands.command(name = 'player', description = "View a player's profile")
  async def player(self, interaction: discord.Interaction, tag = str = None, user = discord.Member = None):
    member = user if user or interaction.user
    guild_id = interaction.guild_id
    await interaction.response.defer()
    await asyncio.sleep(5)
    if tag is None:
      tag = self.load_tag(guild_id).get(str(member.id))
        if tag is None:
          embed = discord.Embed(
            title = 'Houston, we have a problem!',
            description = 'Unfortunately, I could not find a player tag to pull a profile for!',
            color = 0xBF713D
          )
          await interaction.followup.send(embed.embed, ephemeral = True)
    try:
      player = self.brawlstars.get_player(tag)
      embed = discord.Embed(
        title = f"{player.name}'s ({player.tag}) Brawl Stars Profile",
        color = 0xBF713D
      )
      embed.add_field(name = '<:trophy:1186880750428094584> Current Trophies:', value = f'**{player.trophies}**', inline = False)
      embed.add_field(name = '<:trophy:1186880750428094584> Highest Trophies:', value = f'**{player.highest_trophies}**', inline = False)
      embed.add_field(name = '<:club:1186882121286037544> Club Name:', value = f'**{player.club.name}**', inline = False)
      embed.add_field(name = '<:doug:1186883368701403136> Num of Brawlers:', value = f'**{len(player.brawlers)}**', inline = False)
      await interaction.followup.send(embed = embed, ephemeral = True)
    except brawlstats.ServerError as e:
      embed = discord.Embed(
        title = 'Houston, we have a problem!',
        description = f'Unable to connect to Brawl Stars Server! Please try again later!',
        color = 0xBF713D
      )
      print('\n'f'Error connecting to server: {e}')
      await interaction.followup.send(embed = embed, ephemeral = True)
    except brawlstats.RequestError as e:
      embed = discord.Embed(
        title = 'Houston, we have a problem!',
        description = 'Unable to process your request at this time! Please try again later!',
        color = 0xBF713D
      )
      print('\n'f'Error requesting data from API: {e}')
      await interaction.response.send(embed = embed, ephemeral = True)
  
  @app_commands.command(name = 'view', description = 'View the player tag of a user')
  async def view(self, interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.defer()
    member = member if member or interaction.user
    tag = self.players_with_tag.get(str(user.id), "No Tag Set")
    await asyncio.sleep(3)
    embed = discord.Embed(
      title = f"Brawl Stars Player Tag for {member.name}",
      description = f'Tag: {tag}',
      color = 0xBF713D
    )
    await interaction.followup.send(embed = embed, ephemeral = True)

  #@app_commands.command(name = 'battles'

async def setup(bot):
  await bot.add_cog(Brawlv2(bot))

    
        
