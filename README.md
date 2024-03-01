# Description
tg_raidbot is a configurable Telegram raid summary bot for RDM or Golbat database.

# Features
- Configurable message templates with some keywords (see '[templates]' chapter in `config.toml.example`)
- Configurable time format for raid start / end times
- Multiple languages supported for raidnames, pokemon names and attacks: de, en, es, fr, hi, id, it, ja, ko, pl, pt-br, ru, sv, th, tr, zh-tw
- Chat topics support (see [Telegram-Blog](https://www.telegram.org/blog/topics-in-groups-collectible-usernames))
  - Remark: you need to enable thsi feature first in group setting -> enable 'Topics' switch
- Multiple raid chats, each with following individual configuration:
  - choose, if raids are grouped by raid level or only ordered by time
  - choose time order (latest or earliest end time first)
  - Koji geofence (highly recommended) or manual geofence coordlist
  - include or exclude raid eggs
  - automatically pin message (activate or deactivate)
- Koji geofence support

# Limitations
Only RDM and Golbat is supported for now. Extension to support additional scanner systems should be easy by extending `scannerconnector.py`. PRs welcome.

# Installation
It is highly recommended to use virtual python environment (example here with virtualenv plugin).
- create environment: `virtualenv -p python3 ~/<your-venv-folder>/tg_raidbot_env`
- clone github repo: `git clone https://github.com/hamster007Github/tg_raidbot.git`
- cd `tg_raidbot`
- install dependencies:`~/<your-venv-folder>/tg_raidbot_env/bin/pip3 install -r requirements.txt`
- `cp config.toml.example config.toml`
- adapt config.toml for your needs
- run script: `~/<your-venv-folder>/tg_raidbot_env/bin/python3 run.py`

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

### example 1
- public channel: @blub
- show raids level 5 and 6 (mega) including raid eggs grouped by raid level. First level 5, second level 6
- raids with earliest end time should be showed first
- only raids in Koji geofence `newyork`. Note: Geofence with name `newyork` needs to be provided by configurated `[koji]` -> `api_link`

```
[[raidconfig]]
chat_id = "@blub"
raidlevel = [5,6]
eggs = true
raidlevel_grouping = true
order_time_reverse = false
geofence_koji = "newyork"
```
### example 2
- private group chat_id: -987654321
- show only already started raids level 1, 2 and 3 not grouped by raid level, only by time
- raids with latest end time should be showed first
- only raids in rectangular geofence between lat:40.0 lon:7.0 and lat:50.0 lon:8.0

```
[[raidconfig]]
chat_id = "-987654321"
raidlevel = [3,2,1] # remark: order will have no effect, because of 'raidlevel_grouping = false'
eggs = false
raidlevel_grouping = false
order_time_reverse = true
geofence = "40.0 7.0, 40.0 8.0, 50.0 8.0, 50.0 7.0, 40.0 7.0"
```

# Credits
[WatWowMap/pogo-translations](https://github.com/WatWowMap/pogo-translations), where the pogo translation data are fetched from.
