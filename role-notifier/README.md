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

## Configuration

#### config.cfg

```cfg
[ROLE_NOTIFIER]
enabled = true <- If this extension should be enabled, set to `false` to disable.
specific = false <- If the bot should only dm for specific roles. (requires the `role param`)
roles = first_role_id, second_role_id, ... <- The role ids for the specific value. (delimited by a `, `)
```

#### lang.py

```py
role_notifier = {
    "added": {
        "title": "Role received!", <- The title for the embed.
        "content": "You have received the <@{role.id}> ({role.name}) role in {guild.name}!", <- The message for the embed. (valid format values are: {user.*}, {role.*}, {guild.*})
        "footer": {
            "text": "Role Notifier", <- The footer message.
            "icon": "{guild.icon_url}", <- The footer icon. (Valid format argument: {guild.*} | must be a valid url)
            "timestamp": True <- If a dynamic timestamp should be applied to the footer.
        },
        "color": {
            "random": False, <- If this is `True` the embed color will be random.
            "color": 0x00ff00 <- The embed color, requires `random` to be `False`. (0x represents the # in a hex value)
        }
    },
    "removed": { ... } <- same principe
}
```

