from __future__ import annotations

from tools.Config import *
from discord.ext.commands import *

from tools.Steal import Steal

if __name__ == "__main__":
	bot = Steal()
	bot.run(Auth.token)
      
