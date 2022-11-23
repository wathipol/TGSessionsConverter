from telethon import TelegramClient as AsyncTelethonTelegramClient
from telethon.sync import TelegramClient as SyncTelethonTelegramClient
from pyrogram import Client as PyrogramTelegramClient
from telethon.sessions import MemorySession, SQLiteSession
from pyrogram.storage import MemoryStorage, FileStorage, Storage
from telethon.crypto import AuthKey
from telethon.version import __version__ as telethon_version
from pathlib import Path
from stream_sqlite import stream_sqlite
from typing import Union
import io
import asyncio
import base64
import struct
import platform
import sqlite3


class TelegramSession:

    DEFAULT_DEFICE_MODEL: str = "TGS {}".format(platform.uname().machine)
    DEFAULT_SYSTEM_VERSION: str = platform.uname().release
    DEFAULT_APP_VERSION: str = telethon_version
    
    def __init__(self, auth_key: bytes, dc_id, server_address, port, api_id: int, api_hash: str):
        self._auth_key = auth_key
        self._dc_id = dc_id
        self._server_address = server_address
        self._port = port
        self._api_id = api_id
        self._api_hash = api_hash
        self._loop = self.make_loop()

    @property
    def api_id(self):
        if self._api_id is None:
            raise ValueError("api_id is required for this method")
        return self._api_id

    @property
    def api_hash(self):
        if self._api_hash is None:
            raise ValueError("api_hash is required for this method")
        return self._api_hash

    @api_id.setter
    def api_id(self, value):
        self._api_id = value

    @api_hash.setter
    def api_hash(self, value):
        self._api_hash = value
    
    @staticmethod
    def make_loop():
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    @staticmethod
    def from_sqlite_session_file_stream(
            sqlite_session: io.BytesIO, api_id: int, api_hash: str):
        """ Create  <TelegramSession> object from io.BytesIO object of read telethon session file(sqlite)
                return TelegramSession object
                    if sqlite_session is valid open as BytesIO telethon session
                        else -> None
        """
        if not isinstance(sqlite_session, io.BytesIO):
            raise TypeError(
                "sqlite_session must be io.BytesIO object of open and read sqlite3 session file")
        auth_key = None
        dc_id = None
        server_address = None
        port = None

        for table_name, table_info, rows in stream_sqlite(sqlite_session, max_buffer_size=1_048_576):
            if table_name != "sessions":
                continue
            for row in rows:
                if hasattr(
                        row, "auth_key") and hasattr(
                            row, "dc_id") and hasattr(row, "server_address") and hasattr(row, "port"):
                    if row.auth_key is None:
                        continue
                    auth_key = row.auth_key
                    dc_id = row.dc_id
                    server_address = row.server_address
                    port = row.port
                    break
        if (auth_key is None) or (dc_id is None) or (server_address is None) or (port is None):
            return
        return TelegramSession(auth_key, dc_id, server_address, port, api_id, api_hash)

    @staticmethod
    def from_sqlite_session_file(id_or_path: Union[str, io.BytesIO], api_id: int, api_hash: str):
        sqlite_session = id_or_path
        if isinstance(id_or_path, str):
            try:
                with open(id_or_path, "rb") as file:
                    sqlite_session = io.BytesIO(file.read())
            except FileNotFoundError as exp:
                try:
                    with open("{}.session".format(id_or_path), "rb") as file:
                        sqlite_session = io.BytesIO(file.read())
                except Exception:
                    raise exp
        else:
            if not isinstance(id_or_path, io.BytesIO):
                raise TypeError("id_or_path must be str name")

        return TelegramSession.from_sqlite_session_file_stream(sqlite_session, api_id, api_hash)

    @staticmethod
    def from_telethon_or_pyrogram_client(
            client: Union[
                AsyncTelethonTelegramClient, SyncTelethonTelegramClient, PyrogramTelegramClient]):
        if isinstance(client, (AsyncTelethonTelegramClient, SyncTelethonTelegramClient)):
            # is Telethon
            api_hash = str(client.api_hash)
            if api_hash == str(client.api_id):
                api_hash = None
            return TelegramSession(
                client.session.auth_key.key,
                client.session.dc_id,
                client.session.server_address,
                client.session.port,
                client.api_id, api_hash
            )
        elif isinstance(client, PyrogramTelegramClient):
            pass
        else:
            raise TypeError("client must be <telethon.TelegramClient> or <pyrogram.Client> instance")

    @classmethod
    def from_tdata(
            cls, path_to_folder: str, api_id: int, api_hash: str,
            device_model: str = None, system_version: str = None, app_version: str = None):
        from opentele.td import TDesktop
        from opentele.api import CreateNewSession, APIData
        tdesk = TDesktop(path_to_folder)
        api = APIData(
            api_id=api_id,
            api_hash=api_hash,
            device_model=device_model or cls.DEFAULT_DEFICE_MODEL,
            system_version=system_version or cls.DEFAULT_SYSTEM_VERSION,
            app_version=app_version or cls.DEFAULT_APP_VERSION
        )
        loop = cls.make_loop()

        async def async_wrapper():
            client = await tdesk.ToTelethon(None, CreateNewSession, api)
            await client.connect()
            session = TelegramSession.from_telethon_or_pyrogram_client(client)
            session.api_id = api_id
            session.api_hash = api_hash
            await client.disconnect()
            return session

        task = loop.create_task(async_wrapper())
        session = loop.run_until_complete(task)
        return session

    def _make_telethon_memory_session_storage(self):
        session = MemorySession()
        session.set_dc(self._dc_id, self._server_address, self._port)
        session.auth_key = AuthKey(data=self._auth_key)
        return session

    def _make_telethon_sqlite_session_storoge(
            self, id_or_path: str = "telethon", update_table=False, save=False):
        session_storage = SQLiteSession(id_or_path)
        session_storage.set_dc(self._dc_id, self._server_address, self._port)
        session_storage.auth_key = AuthKey(data=self._auth_key)
        if update_table:
            session_storage._update_session_table()
        if save:
            session_storage.save()
        return session_storage

    def make_telethon(
            self, session=None, sync=False, **make_args) -> Union[
                AsyncTelethonTelegramClient, SyncTelethonTelegramClient]:
        """
            Create <telethon.TelegramClient> client object with current session data
        """
        if session is None:
            session = self._make_telethon_memory_session_storage()
        THClientMake = AsyncTelethonTelegramClient
        if sync:
            THClientMake = SyncTelethonTelegramClient
        return THClientMake(session, self.api_id, self.api_hash, **make_args)

    async def make_pyrogram(self, session_id: str = "pyrogram", **make_args):
        """
            Create <pyrogram.Client> client object with current session data
                using in_memory session storoge
        """
        th_client = self.make_telethon()
        if not th_client:
            return
        async with th_client:
            user_data = await th_client.get_me()

        pyrogram_string_session = base64.urlsafe_b64encode(
            struct.pack(
                Storage.SESSION_STRING_FORMAT,
                self._dc_id,
                self.api_id,
                False,
                self._auth_key,
                int(user_data.id or 999999999),
                0
            )
        ).decode().rstrip("=")
        client = PyrogramTelegramClient(
            session_id, session_string=pyrogram_string_session,
            api_id=self.api_id, api_hash=self.api_hash, **make_args)
        return client

    def make_sqlite_session_file(
            self, client_id: str = "telegram",
            workdir: str = None, pyrogram: bool = False,
            api_id: int = None, api_hash: str = None) -> bool:
        """ Make telethon sqlite3 session file
                {id.session} will be created if id_or_path is not the full path to the file
        """
        session_workdir = Path.cwd()
        if workdir is not None:
            session_workdir = Path(workdir)
        session_path = "{}/{}.session".format(session_workdir, client_id)
        
        if pyrogram:
            session_workdir = Path.cwd()
            if workdir is not None:
                session_workdir = Path(workdir)

            # Create pyrogram session
            client = PyrogramTelegramClient(
                client_id, api_id=api_id or self.api_id, api_hash=api_hash or self.api_hash)
            client.storoge = FileStorage(client_id, session_workdir)
            client.storage.conn = sqlite3.Connection(session_path)
            client.storage.create()

            async def async_wrapper(client):
                user_id = 999999999
                th_client = self.make_telethon(sync=False)
                if th_client:
                    async with th_client:
                        user_data = await th_client.get_me()
                        user_id = user_data.id

                await client.storage.dc_id(self._dc_id)
                await client.storage.api_id(self.api_id)
                await client.storage.test_mode(False)
                await client.storage.auth_key(self._auth_key)
                await client.storage.user_id(user_id)
                await client.storage.date(0)
                await client.storage.is_bot(False)
                await client.storage.save()
            
            self._loop.run_until_complete(async_wrapper(client))
        else:
            self._make_telethon_sqlite_session_storoge(session_path, update_table=True, save=True)
        return True

    def make_tdata_folder(self, folder_name: str = "tdata"):
        pass
