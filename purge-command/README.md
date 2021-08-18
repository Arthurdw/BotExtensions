# Purge Command

###### A proper way to clear spam.

## Installation

Open your `config.cfg` file in the `config` folder and paste the following content 
at the bottom of the file or add the line to your existing `MODERATION` section.

```cfg
; The id's of the roles whom are allowed to execute a certain command. ;
[MODERATION]
purge = RoleName, 123456789987654321
```

Open your `lang.py` file in the `config` folder and paste the following content
in that file.

```py
purge_command = {
    "from": "from",
    "started": "Started removing a maximum of {count} messages{ending}.",
    "finished": "Removed {count} messages{ending}",
    "finished_color": 0x00ff00
}
```

## Configuration

#### config.cfg

```cfg
[MODERATION]
purge = RoleName, 123456789987654321 <- The roles/role ids whom may execute the command. (delimited by a ,)
```
