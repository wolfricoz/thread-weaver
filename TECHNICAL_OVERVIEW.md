# Thread Weaver — Technical Overview

A pre-revamp technical review of everything the bot currently covers: architecture, subsystems, data model, feature surface, background jobs, the web API, and existing rough edges. Naming is inconsistent in the codebase — `project/data.py` sets `BOT_NAME = "Thread Weaver"`, but many runtime strings still say **"Forum Manager"** and **"Banwatch"** (a prior project this was forked/adapted from).

- **Version:** `0.5: Alpha` (`project/data.py`)
- **Domain:** Discord **forum-channel** management — automoderation, automated cleanup, archiving/export, notifications, per-guild config.

---

## 1. Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.13+ |
| Discord | `discord.py` (app commands / cogs / `LayoutView` UI v2) |
| Web | FastAPI + uvicorn (optional, same process) |
| ORM / DB | SQLAlchemy 2.x (typed `Mapped`) on MySQL via `pymysql` |
| Migrations | Alembic (`alembic/versions/`) |
| Regex | Google `re2` (ReDoS-safe) for all user-supplied patterns |
| Images | Pillow (downscale + WebP re-encode for exports) |
| Similarity | `python-Levenshtein` (duplicate-thread detection) |
| Helpers | `discord_py_utilities` (messages/permissions/invites wrappers) |

---

## 2. Runtime & bootstrap (`main.py`)

- `load_environment()` → build engine → `database().create()` (creates DB + tables if missing).
- Intents: `message_content` + `members` enabled (both privileged).
- Two run modes, selected by the `API` env var:
  - `API != "TRUE"` → `bot.run(TOKEN)` (plain bot).
  - `API == "TRUE"` → FastAPI `app` with a `lifespan` that starts the bot as an asyncio task; routers auto-collected from `api.__all__`.
- `setup_hook()` auto-loads every `.py` in `modules/`, `listeners/`, `tasks/` as extensions (convention-based, no manifest).
- `on_ready`: startup DM to dev channel, `AccessControl().reload()`, `bot.tree.sync()` (global sync every boot).
- `on_guild_join`: dev-channel notification with guild/owner/member stats.

---

## 3. Architecture layers

```
main.py                      # entrypoint, FastAPI lifespan, extension autoloader
├─ modules/      (cogs)      # slash-command surface
├─ listeners/    (cogs)      # gateway event handlers (automod, reminders, pings)
├─ tasks/        (cogs)      # discord.ext.tasks loops (queue driver, hourly jobs)
├─ classes/
│  ├─ kernel/               # Singleton, Queue, AccessControl, ConfigData
│  ├─ discordcontrollers/   # controllers orchestrating discord + persistence
│  └─ support/              # ThreadArchive, regex validators, singleton
├─ database/
│  ├─ database.py           # SQLAlchemy models + engine
│  └─ transactions/         # data-access layer (one class per aggregate)
├─ resources/configs/       # ConfigMapping (keys), Limits
├─ data/enums/              # PatternTypes, CleanUpTypes
├─ views/                   # UI: buttons, selects, modals, v2 LayoutViews
└─ api/                     # FastAPI routers (premium, sentry, example)
```

Call flow is consistent: **cog/listener → controller → transactions → SQLAlchemy models**, with side-effecting Discord calls funnelled through the global **Queue**.

---

## 4. Data model (`database/database.py`)

| Table | Key columns | Notes |
|---|---|---|
| `servers` | `id` (guild id, PK), `owner`, `name`, `member_count`, `invite`, `active`, `hidden`, `premium` (datetime, nullable), `owner_id`, `updated_at`, `deleted_at` | Premium is an expiry timestamp; `active`/`deleted_at` drive soft-delete + dashboard sync. |
| `config` | `id`, `guild` (FK→servers, CASCADE), `key`, `value` | Generic key/value config store; **values are strings** (see toggle-parsing note in §11). |
| `forums` | `id` (forum channel id, PK), `server_id` (FK), `name`, `minimum_characters`, `duplicates` (bool), `reminder`, timestamps | One row per registered forum channel. |
| `forum_patterns` | `id`, `forum_id` (FK), `name`, `action`, `pattern` | `action` ∈ `BLACKLIST/BLOCK/WARN/REQUIRED`. Blacklist stores a plain word; others store regex. |
| `forum_cleanup` | `id`, `forum_id` (FK), `key`, `days`, `extra` | `key` ∈ `CleanUpTypes`; `UniqueConstraint(forum_id, key)`. `extra` holds the regex for regex-cleanup. |
| `staff` | `id`, `uid`, `role` | Bot-level staff (`dev` / `rep`) for privileged commands. |

Relationships cascade on delete; `Forums.cleanup` is eager-loaded (`lazy="joined"`).

**Enums**
- `PatternTypes.ForumPatterns`: `BLACKLIST`, `BLOCK`, `WARN`, `REQUIRED`.
- `CleanUpTypes`: `ABANDONED=CLEANUPLEFT`, `OLD=CLEANUPDAYS`, `REGEX=CLEANUPREGEX`, `MISSING=CLEANUPMISSING`, `INACTIVITY=CLEANUPINACTIVITY`.
- `ConfigMapping`: canonical config keys — automod log/warn-log, cleanup enabled/log, restore-archived, log-changes + change-log channel, ping-on-thread (toggle/role/channel).

---

## 5. Kernel subsystems (`classes/kernel/`)

### Singleton (`Queue.py`)
Metaclass-based singleton used by `Queue`, `AccessControl`, `ConfigData`, `AutoMod`. Single shared instance per process — effectively global mutable state.

### Queue — global rate-limit-friendly task queue
- Three priority lanes (high=2 / normal=1 / low=0); `process()` drains high→low.
- Holds **coroutines or callables**; `add()` returns an ETA estimate (0.5s/task).
- Driven by `tasks/QueueTask.py` (`@tasks.loop(seconds=0.5)` calls `Queue().start()`), which processes **one task per tick** with a `task_finished` guard.
- A second 3s loop updates the bot presence with queue status.
- Nearly every mutating Discord call (deletes, edits, sends, archive DMs) is enqueued here to serialize against rate limits.

### AccessControl — staff & premium gating
- In-memory `staff` dict (`{role: [uid]}`) + `premium` list of guild ids, hydrated from DB; `reload()` called on ready and after server sync.
- App-command check factories: `check_access("owner"|"dev"|<rep/all>)`, `check_premium()`, `check_blacklist()` (stub — no user blacklist yet).
- `is_premium(guild_id)` used both as a decorator and inline inside AutoMod / purge / cleanup.

### ConfigData — per-guild config cache
- Loads `config` rows into a nested dict `{guild_id: {KEY: value}}`.
- `get_key()` coerces string values → int/bool heuristically; `get_toggle()` normalizes legacy `ENABLED/DISABLED` **and** newer `TRUE/FALSE/1/0/ON/OFF`.
- `get_channel()` resolves a configured channel id with fetch-retries and graceful fallback (first accessible channel → owner DM).
- `migrate()` imports legacy per-guild JSON config files from a `configs/` dir into the DB.

---

## 6. Feature surface

### 6.1 Forum AutoMod (`listeners/ThreadAutoMod.py` + `classes/.../AutoMod.py`)
Event-driven moderation on registered forums. Triggers: `on_message`, `on_message_edit`, `on_thread_create`.

- Thread-starter detection: a forum starter message has `message.id == thread.id` (avoids the THREAD_CREATE/MESSAGE_CREATE ordering race — documented in the listener).
- Staff bypass: Administrator / Manage Messages / Manage Guild / Manage Channels → `ALLOW`.
- Check order (cheap→expensive, first hit wins):
  1. `SHORT` — minimum character requirement (free).
  2. `BLACKLIST` → `BLOCK` — plain-word substring match (free).
  3. `BLOCK` regex patterns (premium).
  4. `WARN` regex patterns — logs, does not delete (premium).
  5. `REQUIRED` regex — starter must contain pattern, else block (premium, first message only).
  6. `DUPLICATE` — Levenshtein ratio ≥ 0.7 vs. same author's other active **and** archived threads (premium).
- Actions (`AutoModActions`): delete message/thread, DM author an `AutomodLayout` (UI v2) explanation, log to automod (or warn) channel.
- Per-guild enabled-forum cache (`_cache`), cleared hourly and on add/remove.
- `on_thread_create` also fires the **ping-on-thread** notification (configurable channel + optional role ping).

### 6.2 Forum management — `/forum` (`modules/Forums.py`)
`add`, `add_all`, `remove`, `blacklist_word` (add/remove/list), `minimum_characters`, `reminder` (auto-posted per new thread), `patterns` (Delete/Warn/Required regex, premium), `duplicates` (premium), `stats`, `recover` (unarchive), `copy` (clone forum + tags + settings), `copytags`, `purge` (confirm + optional owner DM + optional premium archive of each thread). Most gated on Manage Guild/Channels.

### 6.3 Automated cleanup — `/cleanup` (`modules/CleanUp.py` + `ForumTaskActions.py`)
Per-forum rules, premium + Manage Channels + guild-wide `CLEANUP_ENABLED` toggle. Rules: `abandoned` (author left), `old` (age > N days), `inactivity` (no activity N days), `missing_starter`, `regex` (delete matching messages, keep thread). Evaluated hourly by `ForumTask`; removed threads optionally archived to the cleanup-log channel and the owner DM'd a reason.

### 6.4 Archiving / export — `/export` (`modules/Export.py` + `classes/support/ThreadArchive.py`)
`export thread|forum|channel`, premium + Manage Threads, delivered to invoker DMs.
`ThreadArchive` engine:
- Renders each thread to standalone HTML (messages, embeds w/ fields/images/footers, attachments) sharing one `export.css`.
- Image pipeline: SHA-256 dedupe → Pillow downscale (≤1600px) + WebP q80, keep-smaller; skips GIF/SVG/WebP.
- Zip: DEFLATE text, STORE already-compressed images.
- Rich `report()`/embed: counts, size, savings breakdown (dedup/re-encode/zip), date range, elapsed.
- **>24 MB** → uploads to external download backend (`DOWNLOAD_URL_BACKEND`/`DOWNLOAD_API`), returns one-time password-protected link instead of a Discord attachment.
- Also reused by purge and cleanup for their archive-on-delete paths.

### 6.5 Notifications & thread lifecycle
Ping-on-new-thread (channel + role), per-forum reminders, `RESTORE_ARCHIVED` auto-unarchive (capped ~950 active threads), manual `/archive_threads` (`modules/General.py`).

### 6.6 Configuration — `/config` (`modules/Config.py`)
`channels` (perm-validated), `roles`, `toggles`. Optional config-change auditing to a change-log channel via the Queue.

### 6.7 Onboarding (`views/v2/OnboardingLayout.py`)
UI v2 flow on join: Automatic setup (`ConfigSetup.automated_setup`), Manual (`/config`), Dashboard link, docs + support-server links.

### 6.8 Dev / owner — `/dev` (`modules/Dev.py`)
`reload` (env), `add_staff`/`remove_staff`, `announce` (broadcast to all guilds), `leave_server`, `stop`. Owner id from `OWNER` env; staff from the `staff` table.

### 6.9 Logging (`modules/logs.py`)
Per-day rotating log files (auto-prune >7 days), `SafeFormatter` + gateway filter to prevent discord.py logging crashes, centralized app/text command error handlers (friendly user messages + traceback file to dev channel), command-usage auditing.

---

## 7. Background tasks (`tasks/`, all `discord.ext.tasks`)

| Loop | Interval | Job |
|---|---|---|
| `QueueTask.queue` | 0.5s | Drive the global Queue (1 task/tick). |
| `QueueTask.display_status` | 3s | Update presence with queue status. |
| `ForumTask.check_forums_task` | 1h | Run cleanup + archived-recovery across all guild forums. |
| `ForumTask.clear_cache` | 1h | Clear AutoMod enabled-forum cache. |
| `ServerTasks.update_servers` | 1h | Reconcile `servers` table (active/name/owner/count), sync dashboard, reload AccessControl. |

---

## 8. Web API (`api/`, FastAPI, opt-in via `API=TRUE`)

| Route | Auth | Purpose |
|---|---|---|
| `PUT /premium/update` | `Auth().verify()` (bearer) | Sync per-guild premium expiry from external billing. |
| `GET /sentry-debug` | none | Deliberate error to test Sentry. |
| `example` router | — | Template routes. |

FastAPI is configured with docs/redoc/openapi disabled. Also integrates a web **dashboard** (`classes/dashboard/Servers.py` sync) and the external archive **download service**.

---

## 9. External integrations & configuration

- **MySQL** (`DB_*` env).
- **Discord** (`TOKEN`, `OWNER`, `DEVCHANNEL`, `DEV`, `GUILD`, `DASHBOARD_URL`).
- **Download service** (`DOWNLOAD_URL_BACKEND`, `DOWNLOAD_URL_FRONTEND`, `DOWNLOAD_API`) for large exports.
- **Dashboard** sync target.
- **Sentry** (optional) error tracking.
- Env access via `data/env/loader.py` (`env()` + `load_environment()`); tests use `.env.test`.

---

## 10. Tests & docs

- `tests/` — `run_tests.py` plus module tests for forum & staff transactions (`tests/test_modules/`). Coverage is thin (transactions only; no command/automod/archive tests).
- `docs/` — Jekyll (`_config.yml`) command reference (`docs/commands/*.md`) + `docsGenerator.py` and a `commands_cache.json`.

---

## 11. Known rough edges / tech-debt (observed, not exhaustively audited)

Worth resolving as part of the revamp:

- **Identity/naming drift.** "Thread Weaver" vs. "Forum Manager" vs. "Banwatch" across user-facing strings (`Dev.py` announce copy, `main.py` join msg, `ConfigData.get_channel`, onboarding). Also `/dev add_staff` help text says "Banwatch staff."
- **Duplicate method names within cogs shadow earlier commands.** In `Forums.py`, `blacklist_word` is defined twice (the second is actually the `reminder` command) and `copy` is defined twice (`copy` and `copytags`); in `CleanUp.py`, `old` is defined twice (`old` and `inactivity`). Same Python attribute name → the earlier bound method is overwritten. This is a latent registration bug and should be given unique method names.
- **`get_key` truthiness parsing.** `value.lower() in ["true","1","ENABLED"]` — the uppercase `"ENABLED"` can never match a lowercased value; toggle logic largely lives in `get_toggle` instead, so this path is inconsistent.
- **`purge` confirmation isn't gated on the result.** `ConfirmButtons().send_confirmation(...)` is awaited but its return value isn't checked before deleting threads (compare with `/export`, which does check).
- **`Config.toggles`** returns a `send_response(...)` coroutine without `await` in the `send_join_message` branch (and references a `send_join_message`/lobby feature that doesn't exist in this codebase).
- **Premium enforcement is split** between the `@check_premium()` decorator and inline `is_premium()` checks — inconsistent surface.
- **Global sync every boot** (`bot.tree.sync()` in `on_ready`) is rate-limit-heavy; consider guild sync in dev / conditional sync.
- **Singletons as global mutable state** (Queue/AccessControl/ConfigData/AutoMod) — fine now, but a scope-widening revamp should consider testability/lifecycle.
- **Sparse validation feedback**: several regex-validation branches (`add_pattern`, cleanup `regex`) send an error response but then continue executing rather than returning.
- **Dead/placeholder code**: `Dev.send_modal` is a `pass` stub used by `/dev announce`; `check_blacklist` is a stub; `api/example.py` and `sentry-debug` are template leftovers.
