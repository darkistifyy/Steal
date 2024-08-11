from __future__ import annotations

import discord
from discord.ext import commands
from tools.Config import *
from discord import Color
from discord.ext.commands import *
import time
import datetime
import asyncio
import os

from tools.Steal import Steal
from managers.context import StealContext
from discord.ext import commands

def get_bot_metrics(bot: Steal):
    start_time = datetime.datetime.utcnow()
    latency = bot.latency * 1000  
    user_count = len(bot.users)
    server_count = len(bot.guilds)
    uptime = datetime.datetime.utcnow() - start_time
    return latency, user_count, server_count, uptime

if __name__ == "__main__":
	bot = Steal()
	bot.run(Auth.token)
      
