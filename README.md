<img src="https://cdn4.iconfinder.com/data/icons/social-media-and-logos-12/32/Logo_telegram_Airplane_Air_plane_paper_airplane-33-256.png" align="right" width="131" />

# TGSessionsCoverter
![PyPI](https://img.shields.io/pypi/v/TGSessionsCoverter)
![PyPI - License](https://img.shields.io/pypi/l/TGSessionsCoverter)


This module is small util for easy converting Telegram sessions  to various formats (Telethon, Pyrogram, Tdata)
<hr/>


## Installation
```
$ pip install TGSessionsCoverter
```

## Quickstart

1. in the first step: Converting your format to a TelegramSession instance

```python
from tg_converter import TelegramSession
import io

API_ID = 123
API_HASH = "Your API HASH"

# From SQLite telethon\pyrogram session file
session = TelegramSession.from_sqlite_session_file("my_session_file.session", API_ID, API_HASH)

# From SQLite telethon\pyrogram session file bytes stream (io.BytesIO)
with open("my_example_file.session", "rb") as file:
    session_stream = io.BytesIO(file.read())
session = TelegramSession.from_telethon_sqlite_stream(session_stream, API_ID, API_HASH)
```

2. Converting TelegramSession instance to the format whats you need

```python
from tg_converter import TelegramSession

session = TelegramSession(...) # See first step to learn how to create from various formats

# To telethon client
client = session.make_telethon(sync=True) # Use MemorySession as default, see docs
client.connect()
client.send_message("me", "Hello, World!")
client.disconnect()

# To telethon session file (SQLite)
session.make_telethon_session_file("telethon.session")
```

## Docs

### How it works
> An authorization session consists of an authorization key and some additional data required to connect. The module simply extracts this data and creates an instance of TelegramSession based on it, the methods of which are convenient to use to convert to the format you need.



### TelegramSession

...

### Converting to the format whats you need

...


## TODO

- [x] From telethon\pyrogram SQLite session file
- [x] From telethon\pyrogram SQLite session stream
- [ ] From tdata
- [x] To telethon client object (Sync\Async)
- [x] To telethon SQLite session file
- [ ] To pyrogram client object
- [ ] To pyrogram SQLite session file
- [ ] To tdata
- [ ] CLI usage