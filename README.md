# Warframe GiveawayBot
Warframe GiveawayBot is a ground up rewrite of the existing [GiveawayBot](https://giveawaybot.party/), used widespread throughout Discord to host giveaways.

Because I wasn't satisfied with certain limitations around GiveawayBot (such as limits on how many giveaways you can host per channel, for some reason), 
I thought it'd be good coding practice if I learned how to write my own bot that did the very same thing. 

Although the code is open-source, the main purpose is to make sure I can receive feedback while showcasing its progress, rather than off-server deployment.
It's not meant to be used anywhere else asides from the (un)official 
[Warframe Giveaways server](https://discord.gg/fPBKr6dRnK).

To streamline and simplify the usage of some commands (such as calling values from the donation spreadsheet), I've had to hardcode some values in. 
I've still tried my best to make the bot function properly as if it were going to be deployed in multiple places, but if you want to do so, 
you would probably have to tweak said internal values by hand. 

# Features
- An internal database, with data fetched and retrieved using aiosqlite
- Data cached bi-hourly with Google's Python API
- A lot of pain, and probably a bit of swearing

**Commands**

Note: Not all commands are currently implemented, partially or fully. This section is subject to *heavy* change.

`/plat` - Count how much platinum you've donated in total to the server.

`/giveaway` - Start a giveaway for items. 

`/donation` - Donate items to the Warframe Giveaway server. 
