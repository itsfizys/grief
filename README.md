# Grief Discord Bot

A modular Discord bot for moderation, anti-raid protection, server management,
and utilities.

<p align="center">
  <a href="https://www.python.org/downloads/release/python-3120/">
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge" alt="Python 3.12">
  </a>
  <a href="https://discordpy.readthedocs.io/">
    <img src="https://img.shields.io/badge/discord.py-2.7.1-5865F2?style=for-the-badge" alt="discord.py 2.7.1">
  </a>
  <a href="https://www.postgresql.org/">
    <img src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=for-the-badge" alt="PostgreSQL">
  </a>
  <a href="https://github.com/accurs/bleed.git">
    <img src="https://img.shields.io/badge/Upstream-accurs%2Fbleed-181717?style=for-the-badge" alt="Upstream accurs/bleed">
  </a>
</p>

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Starting the bot](#starting-the-bot)
- [Help and owner access](#help-and-owner-access)
- [Startup behavior](#startup-behavior)
- [Project layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [Origin](#origin)

## Features

Commands are grouped into cogs, which the bot loads from the `cogs/` directory.

| Cog | Purpose |
| --- | --- |
| `antiraid` | Anti-raid protections and related server safeguards |
| `fun` | Lightweight entertainment commands |
| `information` | Bot, user, member, and server information |
| `miscellaneous` | Utilities such as AFK messages, polls, embeds, pins, and suggestions |
| `moderation` | Moderation and channel-management commands |
| `owner` | Bot-owner administration and maintenance commands |
| `server` | Server configuration and management |
| `snipe` | Deleted-message, edited-message, and reaction-snipe commands |

Other included behavior:

- A custom help menu organizes visible commands by cog.
- The Owner help category and owner-only commands are visible only to IDs in
  `CLIENT.OWNER_IDS`.
- Configured custom emojis are reconciled with the bot application's emojis
  during startup. Missing emojis are uploaded when possible.
- Guild prefixes are read from PostgreSQL, with `.` as the fallback prefix.

## Requirements

- Python 3.12
- A Discord application with a bot user and a valid bot token
- A reachable PostgreSQL database
- The Python packages listed in `requirements.txt`

The bot requests all Discord gateway intents through `Intents.all()`. In the
Discord Developer Portal, enable the privileged **Server Members**, **Presence**,
and **Message Content** intents for the bot. Invite it with the permissions
required by the commands you plan to use. Include the `applications.commands`
OAuth2 scope if you use application or hybrid commands.

## Setup

### 1. Configure the Discord application

Create a Discord application and bot user, enable the required gateway intents,
and invite the bot to your server. Keep the bot token private.

### 2. Configure the bot and database

The current code reads its settings from `base/config.py`. See
[Configuration](#configuration) for the settings to provide. PostgreSQL must be
reachable by the bot when it starts.

### 3. Install Python dependencies

Create and activate a virtual environment if you are setting up a local copy.

Linux or macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Settings are defined in `base/config.py`.

| Setting | Purpose |
| --- | --- |
| `CLIENT.TOKEN` | Discord bot token used to log in |
| `CLIENT.OWNER_IDS` | List of numeric Discord user IDs allowed to use owner-only commands and see the Owner help category |
| `DATABASE.DSN` | PostgreSQL connection string |
| `DATABASE.MIN_SIZE` | Minimum number of database connections in the pool |
| `DATABASE.MAX_SIZE` | Maximum number of database connections in the pool |
| `EMOJIS` | Custom emoji markup used by bot messages and components |

The imported project currently defines the token and database connection string
in source code. Do not put real credentials in this README or commit them to
source control. Before sharing or publishing the project, move credentials to
a secret manager and update the configuration code to read them there. Rotate
any credentials that have already been exposed.

Only add trusted Discord user IDs to `CLIENT.OWNER_IDS`. The Owner cog includes
administrative actions, and access is enforced by Discord bot-owner checks.

## Starting the bot

From a terminal with the virtual environment active, run:

```bash
python main.py
```

This project runs as a bot process. It does not host a website, dashboard, or
HTTP status endpoint.

## Help and owner access

Use `.help` to open the command menu. The help command also accepts `h`, `cmds`,
and `commands` as aliases. A guild-specific prefix may replace the default `.`.

The Owner category is included only when the requesting user is in
`CLIENT.OWNER_IDS`. Regular users do not see it, and owner-only command checks
still apply when a command is invoked.

## Startup behavior

When `python main.py` runs, the bot:

1. Creates the Discord bot client and logs in.
2. Reconciles configured emojis with the bot application's emojis.
3. Loads extensions from `cogs/`.
4. Loads the Jishaku diagnostic extension.
5. Opens a PostgreSQL connection pool and executes the schema in
   `base/schema/schema.sql`.

Emoji sync logs individual failures and continues when an image cannot be
downloaded or an emoji cannot be uploaded. The database connection is required
for normal startup.

## Project layout

```text
.
|-- README.md
|-- main.py
|-- requirements.txt
|-- base/
|   |-- __init__.py
|   |-- config.py
|   |-- context.py
|   |-- grief.py
|   |-- data/
|   |   `-- pings.txt
|   |-- managers/
|   |   |-- __init__.py
|   |   |-- EmbedBuilder.py
|   |   |-- command.py
|   |   |-- emoji_sync.py
|   |   |-- interaction.py
|   |   |-- paginator.py
|   |   |-- predicates.py
|   |   `-- types.py
|   `-- schema/
|       `-- schema.sql
`-- cogs/
    |-- antiraid/
    |   |-- __init__.py
    |   `-- antiraid.py
    |-- fun/
    |   |-- __init__.py
    |   `-- fun.py
    |-- information/
    |   |-- __init__.py
    |   `-- information.py
    |-- miscellaneous/
    |   |-- __init__.py
    |   `-- miscellaneous.py
    |-- moderation/
    |   |-- __init__.py
    |   `-- moderation.py
    |-- owner/
    |   |-- __init__.py
    |   `-- owner.py
    |-- server/
    |   |-- __init__.py
    |   `-- server.py
    `-- snipe/
        |-- __init__.py
        `-- snipe.py
```

The tree omits repository and environment metadata, installed dependencies, and
generated Python cache files.

## Troubleshooting

- **`ModuleNotFoundError` for a dependency:** confirm Python 3.12 is active and
  install `requirements.txt` in the same environment used to run the bot.
- **Discord login or intent errors:** check the bot token and enable the
  privileged gateway intents in the Discord Developer Portal.
- **Database connection errors:** confirm PostgreSQL is available and that
  `DATABASE.DSN` points to the correct database.
- **An emoji is unavailable:** check the sync log, source emoji ID, application
  emoji limits, and the bot application's access to the Discord API.

## Origin

This project is forked from [accurs/bleed](https://github.com/accurs/bleed.git)
and updated by itsfizys.
