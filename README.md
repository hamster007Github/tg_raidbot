# Description
tg_raidbot is a configurable Telegram raid summary bot for scanner systems like RDM and MAD (currently only RDM is supported).

# Features
- Configurable raid summary message templates with some keywords (see '[templates]' chapter in `config.toml.example`)
- Configurable time format
- Automaticly pinning raid summary message
- Multiple languages supported: de, en, es, fr, hi, id, it, ja, ko, pl, pt-br, ru, sv, th, tr, zh-tw
- Multiple raid chats, each configurable:
  - Choose between raid level grouped raid summary message or only time sorted for each raid chat
  - geofence support
  - include or exclude raid eggs

# Limitations
Only RDM is supported for now. Extension to support additional scanner system should be easy by extending `scannerconnector.py`. PRs welcome.

# Installation
It is highly recommended to use virtual python environment (example here with virtualenv plugin).
- create environment: `virtualenv -p python3 ~/<your-venv-folder>/tg_raidbot_env`
- clone github repo: `git clone https://github.com/hamster007Github/tg_raidbot.git`
- cd `tg_raidbot`
- install dependencies:`~/<your-venv-folder>/tg_raidbot_env/bin/pip3 install -r requirements.txt`
- `cp config.toml.example config.toml`
- adapt config.toml for your needs
- run script: `~/<your-venv-folder>/tg_raidbot_env/bin/python3 eventwatcher.py`

# PM2 example setup
Based on the examples in [Installation](#Installation) you can use following ecosystem file (linux user `myuser`):
```
{
    name: 'tg_raidbot',
    script: 'run.py',
    cwd: '/home/myuser/<your-installation-folder>tg_raidbot',
    interpreter:'/home/myuser/<your-venv-folder>/tg_raidbot_env/bin/python3',
    instances: 1,
    autorestart: true,
    restart_delay: 10000,
    watch: false,
    max_memory_restart: '100M'
}
```

## config.toml options
For now, see `config.toml.example` file. All options are described there.

# Credits
[WatWowMap/pogo-translations](https://github.com/WatWowMap/pogo-translations), where the pogo translation data are fetched from.

