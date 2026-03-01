---
layout: default
title: Configuration

nav_order: 2
---

<h1>Configuration</h1>
<h6>version: 0.1</h6>
<h6>Documentation automatically generated from docstrings.</h6>





<h2>Channels</h2>

### AUTOMOD_LOG
The channel ID where general moderation actions and filter triggers are logged.

### AUTOMOD_WARN_LOG
The channel ID specifically for logging user warnings and infraction thresholds.

### CLEANUP_LOG
The channel ID where summaries of deleted messages and cleanup tasks are sent.

### CHANGES_LOG
The channel ID where the audit trail for config updates is maintained.
<h2>Toggles</h2>

### CLEANUP_ENABLED
Toggle (True/False) to enable or disable the automatic message cleanup service.

### RESTORE_ARCHIVED
Toggle to automatically unarchive or 'bump' threads when they are closed by inactivity.

### LOG_CONFIG_CHANGES
Toggle to enable logging whenever a configuration value is modified via commands.