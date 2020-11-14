# Role Notifications

###### A role update private message extension

## Installation

Open your `config.cfg` file in the `config` folder and paste the following content 
at the bottom of the file.

```cfg
[ROLE_NOTIFIER]
enabled = true
specific = false
roles = first_role_id, second_role_id, ...
```

Open your `lang.py` file in the `config` folder and paste the following content
in that file.

```py
role_notifier = {
    "added": {
        "title": "Role received!",
        "content": "You have received the <@{role.id}> ({role.name}) role in {guild.name}!",
        "footer": {
            "text": "Role Notifier",
            "icon": "{guild.icon_url}",
            "timestamp": True
        },
        "color": {
            "random": False,
            "color": 0x00ff00
        }
    },
    "removed": {
        "title": "Role removed!",
        "content": "The <@{role.id}> ({role.name}) role in {guild.name} has been removed!",
        "footer": {
            "text": "Role Notifier",
            "icon": "{guild.icon_url}",
            "timestamp": True
        },
        "color": {
            "random": False,
            "color": 0xff0000
        }
    }
}
```
