---
title: The afk Plugin
description: Set an Aardwolf title and keep the tells while no client is playing
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - afk
---

# The afk Plugin

The `afk` plugin notices when the last client that can play disconnects. It then sets an AFK title
and keeps the tells that arrive. When a client logs in again it restores the title and says how
many tells wait. It is ported from the `afk` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.afk`:

```text
#bp.core.pluginm.load plugins.aardwolf.afk
```

It depends on the events, settings, triggers, watch, mudcmds, commands and clients core plugins and
on the [connect plugin](connect.md). It never imports another plugin: it keeps its own copies of the
event names. It is not required, so it does not load until asked.

## Behaviour

- **A client that can play** is logged in and not a view client. A client that has not logged in
  yet, and a view-only client, do not count.
- **AFK turns on** when a client disconnects and no client that can play is left. The plugin queues
  `title <afktitle>`.
- **AFK turns off** when a client that can play logs in. A view-only login raises another event and
  keeps AFK on. The plugin queues `title <lasttitle>`, when there is one, and tells the client how
  many tells wait.
- Both changes happen only on a change. Turning AFK on when it is on, or off when it is off, does
  nothing, so no title is sent twice.
- **At load** `isafk` is set from the clients that can play, without sending a title.
- **When the character becomes active** the plugin sends the AFK title while AFK is on, otherwise
  `lasttitle` when it is set. Every title send needs the MUD to be connected.
- **Tells.** The plugin asks for the GMCP `Comm` module. While AFK is on it keeps every
  `comm.channel` message whose `chan` is `tell`, with the time, the sender and the text. The tells
  are saved and survive a restart.
- **The title commands are hidden queued commands.** They go through the mudcmds queue as the type
  `afk_title`. The reply line opens the hide window, which closes at the prompt after the command
  finishes. A title you type yourself is never hidden.
- **The last title.** A watch on the `title` command (`tit`, `titl` and `title` are accepted) keeps
  what a client types. When the MUD confirms it, the typed title becomes `lasttitle`, unless it
  equals `afktitle`: that is the AFK title set by hand. The colour codes are kept.
- **Finishing.** A trigger group is on only while a title is pending. A reply line finishes a
  queued title, or saves a typed one. When no reply matches, the mudcmds timeout frees the queue
  and the group is turned off. A MUD disconnect clears the pending state.

## Settings

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `afktitle` | `is AFK.` | The title set while AFK is on. |
| `lasttitle` | empty | The title restored when AFK ends. Set by a typed title. |
| `isafk` | `False` | The AFK flag. Read only. |

```text
#bp.aardwolf.afk.set afktitle gone for a while
```

Changing `afktitle` while AFK is on does not send it; it is used the next time AFK turns on.

## Commands

| Command | Meaning |
| :--- | :--- |
| `show` | Show the tells kept while AFK. |
| `clear` | Forget the kept tells. |
| `toggle` | Turn AFK on or off by hand, and say which. |

## MUD output

These texts are guessed from the old plugin and are **unconfirmed**. They need a check on a real
character:

1. The reply to a title, `Title now set to: <title>` (`TITLE_SET_REGEX` in
   `src/aardwolf/afk/libs/_afk.py`). It opens the hide window of a queued title and is the reply
   trigger.
2. The abbreviations `tit` and `titl` of the `title` command (`WATCH_TITLE_REGEX`).
3. The reply to a rejected title is not known. It matches nothing, so the queued command ends at
   the mudcmds timeout and the reply is shown.
4. The GMCP `comm.channel` fields `chan` (`tell`), `msg` and `player`.

```text
Title now set to: is AFK.
```

## Storage

The tells are kept in `tells.txt` in the plugin data directory, under the key `queue`, as a list
of entries with `timestamp` (epoch seconds), `player` and `msg`. The file is written when a tell
arrives, on `clear` and when the proxy saves.

## Events

The plugin listens to `ev_plugins.core.clients_client_disconnected`,
`ev_plugins.core.clients_client_logged_in`, `ev_libs.net.mud_gmcp_comm.channel` and
`ev_libs.net.mud_muddisconnect`. It raises no events.

## Old to new

| Old | New |
| :--- | :--- |
| the old `afk` plugin module | `src/aardwolf/afk/` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |
| setting `queue` (a list) | the file `tells.txt`; the setting is dropped |
| event `client_connected` and `client_disconnected` | `clients_client_disconnected` and `clients_client_logged_in` |
| event `GMCP:comm.channel` | `ev_libs.net.mud_gmcp_comm.channel` |
| watch `titleset` | watch `afk_title` |
| `send.execute('title ...')` | a hidden queued `afk_title` command |
| `send.client` | a direct send to the client |

## Changes from the old plugin

1. `show` tested the queue the wrong way round: it said the queue was empty when it held tells.
2. The docstring of `clear` was copied from a colour example plugin.
3. `checkfortell` printed debug lines with `print()`.
4. The queue was a readonly list setting changed in place. Settings now return a copy, so the queue
   moved to a saved dictionary and the `queue` setting is dropped.
5. The GMCP callback was registered when AFK turned on and unregistered when it turned off, but
   only when the MUD was connected, so tells could be kept after AFK ended. One subscription now
   stays, and keeps a tell only while AFK is on.
6. The title was restored only while the MUD was connected, and nothing restored it later. It is
   now also sent when the character becomes active.
7. Turning AFK on sent `title` with no check that the MUD was connected.
8. After the first active the old plugin always sent `lasttitle`, even while AFK. It now sends the
   AFK title then.
9. Turning AFK off sent `title ` with an empty `lasttitle`. Nothing is sent when it is empty.
10. `load` forced `isafk` to false, and every connect and disconnect changed the setting, so titles
    were sent again for an unchanged value. The flag is now set from the clients, and changes only
    on a change.
11. The connect handler counted clients that had not logged in and view-only clients. Only clients
    that can play count.
12. Each typed title registered `trigger_all` and could leave it registered or lose the capture. A
    trigger group is now on only while a title is pending.
13. The `send.msg` debug messages are debug logs.
14. `TITLEMATCH` and `TITLERE` (`Your title is:`) were never used and are dropped.
15. The class docstring said "a plugin to show connection information".
16. `toggle` returned no message. It says whether AFK is on or off.
17. The notice said `You have 1 tells`. It now says `1 tell`.
18. Kept as before: tells are kept only while AFK is on and only for `chan == "tell"`, a typed
    title equal to `afktitle` is not remembered (now compared on what was typed, not on the echo
    from the MUD), and changing `afktitle` while AFK is on does not send it.
19. `checkfortell` raised on a message with no `data`, or with data that was not a dictionary. Such
    a message is ignored.
20. The time of a tell was stored as text. It is stored as epoch seconds and formatted when shown,
    as `%a %b %d %Y %H:%M:%S`.
21. The reply to the title command was visible. The queued title's reply is now hidden; a typed
    title's reply is shown.

## Known gaps

- The MUD texts above are unconfirmed.
- A typed title and a queued title sent at the same moment can be mixed up: the queued title clears
  the pending typed one.
- A title the MUD rejects shows its reply, and the queued command waits for the mudcmds timeout.
