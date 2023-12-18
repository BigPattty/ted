# This is a cog version of a working economy system. Please use it as you wish
import discord
from discord import app_commands
from discord.ext import commands
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

  def check_cooldown(self, user_id, command, cooldown_period):
    current_time = time.time()
    if (user_id, command) in self.cooldowns:
      last_used, cooldown = self.cooldowns[(user_id, command)]
      if current_time - last_used < cooldown:
        return cooldown - (current_time - last_used)
    self.cooldowns[(user_id, command)] = (current_time, cooldown_period)
    return None

  def get_bal(self, guild_id):
    return f'data/bal_{guild_id}.txt'

  def get_log(self, guild_id):
    return f'data/econset_{guild_id}.txt'

  def load_bal(self, guild_id):
    with self.lock:
        path = self.get_bal(guild_id)
        if not os.path.exists(path):
            with open(path, "w") as file:
                json.dump({}, file)
            return {}
        with open(path, "r") as file:
            return json.load(file)


  def save_bal(self, guild_id, bal):
    with self.lock:
        path = self.get_bal(guild_id)
        with open(path, 'w') as file:
            json.dump(bal, file, indent=4)

  def load_log(self, guild_id):
    with self.lock:
        path = self.get_log(guild_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as file:
            data = json.load(file)
            return int(data.get("log_channel_id")) # Ensure it's an integer
 # Assuming this is how your JSON is structured

  def save_log(self, guild_id, channel_id):
    with self.lock:
        path = self.get_log(guild_id)
        data = {'log_channel_id': channel_id}
        with open(path, "w") as file:
            json.dump(data, file, indent=4)



  async def log_to_channel(self, channel_id, command, action, user_ident):
    channel = self.bot.get_channel(channel_id)
    if channel is None:
        print(f"Failed to find channel with ID: {channel_id}")
        return

    embed = discord.Embed(
        title=f'Economy Command - {command}',
        description='The following is a log from the use of an economy command',
        color=0xBF713D
    )
    embed.add_field(name="Action:", value=f'`{action}`', inline=False)
    embed.add_field(name="Perpetrator:", value=f'`{user_ident}`', inline=False)

    await channel.send(embed=embed)



  async def is_admin(self, interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator and await self.bot.is_owner(interaction.user)

  @app_commands.command(name = 'add', description = "Check a user's balance! Don't worry, this is free of charge!")
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
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)
    self.save_bal(guild_id, bal)

    embed = discord.Embed(
      title = 'Credits Added!',
      description = f"Looks like someone just got a nice helping hand of {credits} credits!",
      color = 0xBF713D
    )
    await interaction.response.send_message(embed = embed)

  @app_commands.command(name = 'remove', description = "Check a user's balance! Don't worry, this is free of charge!")
  async def remove(self, interaction: discord.Interaction, member: discord.Member, credits: int):
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
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)
    self.save_bal(guild_id, bal)

    embed = discord.Embed(
      title = 'Credits Removed!',
      description = f"Today obviously wasn't their day today, because they just lost {credits} credits! RIP",
      color = 0xBF713D
    )
    await interaction.response.send_message(embed = embed)

  @app_commands.command(name = 'balance', description = "Check a user's balance! Don't worry, this is free of charge!")
  async def bal(self, interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    guild_id = str(interaction.guild_id)
    bal = self.load_bal(guild_id)
    user_bal = bal.get(str(member.id), 0)
    user_ident = str(interaction.user.id)
    action = f"Looked at the balance of {member.name}"
    command = '/balance'
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)
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
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)

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
    cooldown_remaining = self.check_cooldown(interaction.user.id, "test", 30)
    if cooldown_remaining:
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
    bal[user_id] = bal.get(user_id, 0) + earnings
    self.save_bal(guild_id, bal)
    user_ident = str(interaction.user.id)
    action = f"{interaction.user.name} went to work and earned {bal[user_id]}"
    command = '/work'
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
        await self.log_to_channel(log_channel_id, command, action, user_ident)

      # Create and send an embed
    embed = discord.Embed(
      title = "Payday has arrived!", 
      description = f"Your had work finally paid off and you earned **{earnings}** credits", 
      color = 0xbf713d
    )
    embed.add_field(name = "Your balance is now:", value = f"**{bal[user_id]}** credits", inline = False)
    await interaction.response.send_message(embed = embed)

  @app_commands.command(name='setlogchannel', description='Set a channel for logging economy actions.')
  @app_commands.describe(channel='The channel to set as the log channel')
  @app_commands.guild_only()
  async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
    if not await self.is_admin(interaction):
        embed = discord.Embed(
            title='Whoa there tiger',
            description="Only admin's can do this!",
            color=0xBF713D
        )
        embed.set_footer(text="Nice try!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    self.save_log(guild_id, channel.id)
    user_ident = str(interaction.user.id)
    # Inside the set_log_channel method after saving the new log channel
    log_channel_id = self.load_log(guild_id)
    if log_channel_id:
      action = f"Set the economy log channel to <#{channel.id}>"
      command = '/setlogchannel'
      await self.log_to_channel(log_channel_id, command, action, str(interaction.user.id))


    embed = discord.Embed(
      title = 'Economy Log Set!',
      description = f"The economy log channel for {interaction.guild.name} has been set to <#{channel.id}>",
      color = 0xBF713D
    )
    await interaction.response.send_message(embed = embed)

  

async def setup(bot):
  await bot.add_cog(Economy(bot))
     
