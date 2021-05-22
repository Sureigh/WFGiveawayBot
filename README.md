# Warframe GiveawayBot
Warframe GiveawayBot is a ground up rewrite of the existing [GiveawayBot](https://giveawaybot.party/), used widespread throughout Discord to host giveaways.

Because I wasn't satisfied with certain limitations around GiveawayBot (such as limits on how many giveaways you can
host per channel, for some reason), I thought it'd be good coding practice if I learned how to write my own bot that did
the very same thing.

Although the code is open-source, the main purpose is to make sure I can receive feedback while showcasing its progress,
rather than off-server deployment. It's not meant to be used anywhere else asides from the (un)official
[Warframe Giveaways server](https://discord.gg/fPBKr6dRnK), though I've made it so that with a few tweaks, it should be
able to work anywhere.

To streamline and simplify the usage of some commands (such as calling values from the donation spreadsheet), I've had
to hardcode some values in. I've still tried my best to make the bot function properly as if it were going to be
deployed in multiple places, but if you want to do so, you would probably have to tweak said internal values by hand.

## Features

- An internal database, with data fetched and retrieved using aiosqlite
- Data cached with Google's Python API
- A lot of pain, and probably a bit of swearing

### Commands

Note: Not all commands are currently implemented, partially or fully. This section is subject to *heavy* change.

All commands should be prefixed with `g?` to invoke this. This can be changed in the bot's configuration (WIP)

#### General

- `[command/cmd/c]`
  - `[create/c/new/n] <name> <response>` Create a custom command.
  - `[remove/rm/delete/d] <name>` Remove an existing custom command.
  - `[update/u/edit/e] <cmd> <name> <response>` Update an existing custom command's name, response and/or description.


- `update_sheet` Force updates the cached spreadsheet.

#### Giveaway

- `[plat/p]` - Check how much platinum you've donated to the server.


- `[donation/donate]` - Donate items to the Warframe Giveaway server.


- `[giveaway/give/g]`
  - `[start/s] <channel: optional> <giveaway_info>` Start a new giveaway.
  - `[end/e] <giveaway_id>` End an existing giveaway.
  - `[reroll/r] <giveaway_id>` Reroll a giveaway that has ended.
  - `edit <giveaway_id> <giveaway_info>` Edit an existing giveaway's duration or restriction(s).


- `[disqualify/disq/d]`
  - `[user/u] <user> <duration> <reason: optional>` Disqualify a user from joining giveaways.
  - `[check/c] <user>` Check a user's disqualification history.
  - `[time/t] <user: optional>` Check how long until you, or a user, are re-eligible for giveaways.
