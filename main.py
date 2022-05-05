from telethon import TelegramClient as AsyncTelethonTelegramClient
from telethon.sync import TelegramClient as SyncTelethonTelegramClient
from pyrogram import Client as PyrogramTelegramClient
from telethon.sessions import MemorySession, SQLiteSession
from telethon.crypto import AuthKey
from stream_sqlite import stream_sqlite
from typing import Union
import io


class TelegramSession:
    def __init__(self, auth_key: bytes, dc_id, server_address, port, api_id: int, api_hash: str):
        self._auth_key = auth_key
        self._dc_id = dc_id
        self._server_address = server_address
        self._port = port
        self.api_id = api_id
        self.api_hash = api_hash

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
        pass

    @staticmethod
    def from_tdata(path_to_folder: str):
        pass

    def _make_telethon_memory_session_storage(self):
        session = MemorySession()
        session.set_dc(self._dc_id, self._server_address, self._port)
        session.auth_key = AuthKey(data=self._auth_key)
        return session

    def make_telethon(
            self, session=None, sync=False) -> Union[
                AsyncTelethonTelegramClient, SyncTelethonTelegramClient]:
        """
            Create <telethon.TelegramClient> client object with current session data
        """
        if session is None:
            session = self._make_telethon_memory_session_storage()
        THClientMake = AsyncTelethonTelegramClient
        if sync:
            THClientMake = SyncTelegramClient
        return THClientMake(session, self.api_id, self.api_hash)

    def make_pyrogram(self, session, sync=False):
        pass

    def make_telethon_session_file(self, id_or_path: str = "telethon") -> bool:
        """ Make telethon sqlite3 session file
                {id.session} will be created if id_or_path is not the full path to the file
        """
        session_storage = SQLiteSession(id_or_path)
        session_storage.set_dc(self._dc_id, self._server_address, self._port)
        session_storage.auth_key = AuthKey(data=self._auth_key)
        session_storage._update_session_table()
        session_storage.save()
        return True
