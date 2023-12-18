# This is a cog version of a working economy system. Please use it as you wish
import discord
from discord import app_commands
from discord.ext import commands, BucketType
import os
import json
import threading
import random
import asyncio
import time

class Economy(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.lock = threading.Lock()
    self.cooldowns = {}

  def check_cooldown(user_id, command, cooldown_period):
    current_time = time.time()
    if (user_id, command) in self.cooldowns:
      last_used, cooldown = self.cooldown[(user_id, command)]
      if current_time - last_used < cooldown:
        return cooldown - (current_time - last_used)
    self.cooldown[(user_id, command)] = (current_time, cooldown_period)
    return None

  def get_bal(self, guild_id):
    return f'data/bal_{guild_id}.txt'

  def get_log(self, guild_id):
    return f'econset_{guild_id}.txt'

  def load_bal(self, guild_id):
    with self.lock:
      path = self.get_bal(guild_id)
      if not os.path.exists(path):
        return {}
      with open(path, "r") as file:
        return json.load(file)

  def save_bal(self, guild_id, bal):
    with self.lock:
      path = self.get_bal(guild_id)
      with open(path, 'w') as file:
        json.dump(balance, file, indent = 4)

  def load_log(self, guild_id):
    with self.lock:
      path = self.get_set(guild_id)
      if not os.path.exists(path):
        return None
      with open(path, "r") as file:
        return json.load(file)

  def save_log(self, guild_id, channel):
    with self.lock:
      path = self.get_log(guild_id)
      with open(path, "w") as file:
        json.dump(channel, file, intent = 4)

  async def log_to_channel(self, channel, command, action, user_ident):
    embed = discord.Embed(
      title = f'Economy Command - {command}',
      description = 'The following is a log from the use an economy command',
      color = 0xBF713D
    )
    embed.add_field(name = "Action:", value = f'`{action}`', inline = False)
    embed.add_field(name = "Perpetrator:", value = f'`{user_ident}`', inline = False)
    channel = channel
    await channel.send(embed = embed)

  async def is_admin(self, interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator and interaction.is_owner

  @app_commands.command(name = 'add', description = "Add credits to a user, on us!")
  async def add(self, interaction: discord.Interaction, member: discord.Member, credits: int):
    if not await self.is_admin(interaction):
      embed = discord.Embed(
        title = 'Whoa there tiger',
        description = "No cheating unless your an admin",
        color = 0xBF713D
      )
      embed.set_footer(text = "Nice try!")
      await interaction.response.send_message(embed = embed, ephemeral = True)

    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    bal[str(member.id)] = bal.get(str(member.id),0) + credits
    user_ident = str(interaction.user.id)
    action = f"{credits} credits have been added to {member.name}'s balance via admin command"
    command = '/add'
    channel = self.get_log(guild_id)
    self.log_to_channel(channel, command, action, user_ident)
    self.save_bal(guild_id, bal)

    embed = discord.Embed(
      title = 'Credits Added!',
      description = f"Looks like someone just got a nice helping hand of {credits} credits!",
      color = 0xBF713D
    )
    await interaction.reponse.send_message(embed = embed)

  @app_commands.command(name = 'remove', description = "Remove credits from someone, on us!")
  async def add(self, interaction: discord.Interaction, member: discord.Member, credits: int):
    if not await self.is_admin(interaction):
      embed = discord.Embed(
        title = 'Whoa there tiger',
        description = "No cheating unless your an admin",
        color = 0xBF713D
      )
      embed.set_footer(text = "Nice try!")
      await interaction.response.send_message(embed = embed, ephemeral = True)

    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    bal[str(member.id)] = bal.get(str(member.id),0) - credits
    user_ident = str(interaction.user.id)
    action = f"{credits} credits have been removed from {member.name}'s balance via admin command"
    command = '/remove'
    channel = self.get_log(guild_id)
    self.log_to_channel(channel, command, action, user_ident)
    self.save_bal(guild_id, bal)

    embed = discord.Embed(
      title = 'Credits Removed!',
      description = f"Today obviously wasn't their day today, because they just lost {credits} credits! RIP",
      color = 0xBF713D
    )
    await interaction.reponse.send_message(embed = embed)

  @app_commands.command(name = 'balance', description = "Check a user's balance! Don't worry, this is free of charge!")
  async def bal(self, interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    user_bal = bal.get(str(member.id), 0)
    user_ident = str(interaction.user.id)
    action = f"Looked at the balance of {member.name}"
    command = '/balance'
    channel = self.get_log(guild_id)
    self.log_to_channel(channel, command, action, user_ident)
    sorted_bals = sorted(bal.items(), key = lambda x: x[1], reverse = True)
    user_rank = next((idx for idx, (user_id, _) in enumerate(sorted_bals, start = 1) if user_id == str(member.id)), None)

    embed = discord.Embed(
      title = f"{member.name}'s Server Balance!",
      color = 0xBF713D
    )
    embed.add_field(name = "Credits in Wallet:", value = f"**{user_bal}**", inline = True)
    embed.add_field(name = "Leaderboard Position:", value = f"**#{user_rank}**", inline = True)
    embed.add_field(name = "Credits in Bank:", value = "*Coming Soon!*", inline = True)
    await interaction.response.send_message(embed = embed)

  @app_commands.command(name = 'leaderboard', description = "See who has the top balance in your server!")
  async def user_leaderboard(self, interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    sorted_balances = sorted(bal.items(), key = lambda x: x[1], reverse = True)
    user_ident = str(interaction.user.id)
    action = f"Looked at the leaderboard for {interaction.guild.name}"
    command = '/leaderboard'
    channel = self.get_log(guild_id)
    self.log_to_channel(channel, command, action, user_ident)

    embed = discord.Embed(
      title = f"{interaction.guild.name}'s Leaderboard", 
      description = "Here are your discord try-hards! (Top 10)", 
      color = 0xbf713d
    )
    for idx, (user_id, balance) in enumerate(sorted_balances[:10], start=1):
      member = self.bot.get_guild(int(guild_id)).get_member(int(user_id))
      name = member.display_name if member else f"User ID: {user_id}"
      embed.add_field(name=f"{idx}. {name}", value=f"Balance: **{balance}** credits", inline=False)

    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="work", description="Gotta get the dosh from somewhere")
  async def work(self, interaction: discord.Interaction):
    cooldown_remaining = check_cooldown(interaction.user.id, "test", 30)
    if cooldown_rate:
      embed = discord.Embed(
        title = "Hold your horses!",
        description = f'You just got off work Try again in {cooldown_remaining:.2f} seconds.',
        color = 0xbf713d
      )
      await interaction.response.send_message(embed = embed)
      

    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    user_id = str(interaction.user.id)

      # Calculate earnings
    
    earnings = random.randint(1000, 10000)

      # Update balance
    bal[user_id] = balance.get(user_id, 0) + earnings
    self.save_bal(guild_id, balance)
    user_ident = str(interaction.user.id)
    action = f"{interaction.user.name} went to work and earned {bal[user_id]}"
    command = '/work'
    channel = self.get_log(guild_id)
    self.log_to_channel(channel, command, action, user_ident)

      # Create and send an embed
    embed = discord.Embed(
      title = "Payday has arrived!", 
      description = f"Your had work finally paid off and you earned **{earnings}** credits", 
      color = 0xbf713d
    )
    embed.add_field(name = "Your balance is now:", value = f"**{balance[user_id]}** credits", inline = False)
    await interaction.response.send_message(embed = embed)

async def setup(bot):
  await bot.add_cog(Economy(bot))
     
