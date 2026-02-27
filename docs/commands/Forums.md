---
layout: default
title: Forums
parent: Commands
nav_order: 5
---

<h1>Forums</h1>
<h6>version: 0.1</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Forum management commands


### `add`

**Usage:** `/forums add`

> Adds the chosen forum channel for the bot, enabling the features the bot provides for forum channels.

Permissions:
- Manage guild

---

### `remove`

**Usage:** `/forums remove`

> Removes the chosen forum channel from the bot's database, disabling the features the bot provides for forum channels.

Permissions:
- Manage guild

---

### `add_pattern`

**Usage:** `/forums add_pattern <operation> <name> <pattern> <action>`

> Add / Remove / List patterns for forum threads.

Permissions:
- Manage guild
- Premium access

---

### `blacklist_word`

**Usage:** `/forums blacklist_word <operation> <word>`

> Adds/Removes a word to the forum blacklist [simple]

Permissions:
- Manage guild

---

### `character_count`

**Usage:** `/forums character_count <operation> <character_count>`

> Adds/Removes a minimum character requirement for threads in the selected forums.

Permissions:
- Manage guild

---

### `duplicates`

**Usage:** `/forums duplicates <allow>`

> Allow or disallow duplicate threads in the selected forums. Duplicate threads are threads with the same starter message content. This is determined on a user basis, so different users can create threads with the same content without being considered duplicates.

Permissions:
- Manage guild
- Premium access

---

### `stats`

**Usage:** `/forums stats <forum>`

> Get stats for a forum

---

### `recover`

**Usage:** `/forums recover <forum>`

> Recover archived posts

---

### `copy`

**Usage:** `/forums copy <forum> <name>`

> Copy a forum with all settings!

---

### `add_all`

**Usage:** `/forums add_all`

> Missing Documentation

---

### `purge`

**Usage:** `/forums purge <forum> <notify_user> <archive>`

> Purge all threads in a forum, notify_user returns the contents of the thread to the user that started it.

---

