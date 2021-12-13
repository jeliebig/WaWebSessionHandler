import json
import os.path
from typing import NoReturn, Optional, Union


class IDBObjectStore:
    name: str
    auto_increment: bool
    key_path: list[str]
    __indices: dict[str, bool]
    # data could also be: list[dict[str, any]] - but let's leave it like that for now
    __data: list[dict[str, str]]

    def __is_unique_value(self, index: str, value: Optional[str]) -> bool:
        for entry in self.__data:
            if value == entry[index]:
                return False
        return True

    @staticmethod
    def create_from_dict(os_dict: dict):
        required_keys = ['name', 'autoIncrement', 'keyPath', 'indices', 'data']
        for key in required_keys:
            if key not in os_dict.keys():
                raise KeyError(f'Could not find key "{key}".\n'
                               f'Make sure the dictionary contains all required keys.')
        new_os = IDBObjectStore(os_dict['name'], os_dict['autoIncrement'], os_dict['keyPath'])
        for name, unique in os_dict['indices'].items():
            new_os.create_index(name, unique)
        for data in os_dict['data']:
            new_os.add_data(data)
        return new_os

    def __init__(self, name: str, auto_increment: Optional[bool] = False,
                 key_path: Optional[Union[list[str], str]] = ''):
        self.name = name.strip()
        self.auto_increment = auto_increment
        self.__indices = {}
        self.__data = []
        if isinstance(key_path, str):
            if len(key_path.strip()) > 0:
                self.key_path = [key_path.strip()]
            else:
                self.key_path = []
        elif isinstance(key_path, list):
            self.key_path = key_path
        else:
            self.key_path = []

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'autoIncrement': self.auto_increment,
            'keyPath': self.key_path,
            'indices': self.__indices,
            'data': self.__data
        }

    def create_index(self, name: str, unique: Optional[bool] = False) -> NoReturn:
        if name.strip() not in self.__indices.keys():
            self.__indices[name.strip()] = unique
        else:
            raise ValueError(f'Cannot create duplicate index: {name.strip()}')

    def add_data(self, data: dict[str, Optional[str]]) -> NoReturn:
        for index, value in data.items():
            if index in self.__indices.keys():
                if self.__indices[index]:
                    if not self.__is_unique_value(index, value):
                        raise ValueError(f'Cannot insert data. Duplicate value for unique index: {index}')
        self.__data.append(data)

    def get_data_num(self) -> int:
        return len(self.__data)

    def get_indices_num(self) -> int:
        return len(self.__indices)

    def get_indices(self) -> dict[str, bool]:
        return self.__indices

    def get_data(self) -> list[dict[str, str]]:
        return self.__data


class IDBDatabase:
    name: str
    version: int
    __object_stores: dict[str, IDBObjectStore]

    @staticmethod
    def create_from_dict(db_dict: dict):
        required_keys = ['name', 'version', 'objectStores']
        for key in required_keys:
            if key not in db_dict.keys():
                raise KeyError(f'Could not find key "{key}".\n'
                               f'Make sure the dictionary contains all required keys.')
        new_db = IDBDatabase(db_dict['name'], db_dict['version'])
        for name, object_store in db_dict['objectStores'].items():
            new_db.add_object_store(IDBObjectStore.create_from_dict(object_store))
        return new_db

    def __init__(self, name: str, version: Optional[int] = 1):
        self.name = name.strip()
        if version > 0:
            self.version = version
        else:
            raise ValueError('Version cannot be <= 0')
        self.__object_stores = {}

    def as_dict(self) -> dict:
        db_dict = {
            'name': self.name,
            'version': self.version,
            'objectStores': {}
        }
        for name, object_store in self.__object_stores.items():
            db_dict['objectStores'][name] = object_store.as_dict()
        return db_dict

    def add_object_store(self, object_store: IDBObjectStore) -> NoReturn:
        if object_store.name not in self.__object_stores.keys():
            self.__object_stores[object_store.name] = object_store
        else:
            raise ValueError(f'Cannot add object store. Duplicate name: {object_store.name}')

    def get_object_store_num(self):
        return len(self.__object_stores)

    def get_object_stores(self) -> list[IDBObjectStore]:
        return list(self.__object_stores.values())


class IndexedDB:
    __URL: str
    __databases: dict[str, IDBDatabase]

    @staticmethod
    def create_from_dict(idb_dict: dict):
        required_keys = ['url', 'databases']
        for key in required_keys:
            if key not in idb_dict:
                raise KeyError(f'Could not find key "{key}".\n'
                               f'Make sure the dictionary contains all required keys.')
        new_idb = IndexedDB(idb_dict['url'])
        for name, database in idb_dict['databases'].items():
            new_idb.add_db(IDBDatabase.create_from_dict(database))
        return new_idb

    def __init__(self, url: str):
        self.__URL = url.strip()
        self.__databases = {}

    def as_dict(self) -> dict:
        idb_dict = {'url': self.__URL, 'databases': {}}
        for name, idb_db in self.__databases.items():
            idb_dict['databases'][name] = idb_db.as_dict()
        return idb_dict

    def get_url(self):
        return self.__URL

    def add_db(self, db: IDBDatabase) -> NoReturn:
        if db.name not in self.__databases.keys():
            self.__databases[db.name] = db
        else:
            raise ValueError(f'Cannot add db. Duplicate name: {db.name}')

    def get_db_num(self):
        return len(self.__databases)

    def get_dbs(self) -> list[IDBDatabase]:
        return list(self.__databases.values())

    def get_db(self, name: str) -> IDBDatabase:
        return self.__databases[name]


class SessionObject:
    __NAME: str
    __URL: str
    __FILE_EXT: str
    cookies: dict[str, str]
    local_storage: dict[str, str]
    indexed_db: IndexedDB

    @staticmethod
    def create_from_file(path: str):
        if os.path.isfile(path):
            required_keys = ['name', 'url', 'fileExt', 'cookies', 'localStorage', 'indexedDb']
            with open(path, 'r') as file:
                session_object = json.load(file)

            for key in required_keys:
                if key not in session_object.keys():
                    raise KeyError(f'Could not find key "{key}" in "{path}".\n'
                                   f'Make sure the session file contains all required keys.')

            return SessionObject(
                session_object['name'], session_object['url'], session_object['fileExt'],
                session_object['cookies'], session_object['localStorage'],
                IndexedDB.create_from_dict(session_object['indexedDb'])
            )
        else:
            raise FileNotFoundError(f'Could not find "{path}". No new session object can be created.')

    @staticmethod
    def is_valid_session(param, param1, param2):
        raise NotImplementedError

    def __init__(self, name: str, url: str, ext: str = 'json',
                 cookies: Optional[dict[str, str]] = None,
                 local_storage: Optional[dict[str, str]] = None,
                 indexed_db: Optional[IndexedDB] = None):
        self.__NAME = name.strip()
        self.__URL = url.strip()
        self.__FILE_EXT = ext.strip()
        if cookies:
            self.cookies = cookies
        else:
            self.cookies = {}
        if local_storage:
            self.local_storage = local_storage
        else:
            self.local_storage = {}
        if indexed_db:
            self.indexed_db = indexed_db
        else:
            self.indexed_db = IndexedDB(self.__URL)

    def save_to_file(self, path: str):
        session_object = {
            'name': self.__NAME,
            'url': self.__URL,
            'fileExt': self.__FILE_EXT,
            'cookies': self.cookies,
            'localStorage': self.local_storage,
            'indexedDb': self.indexed_db
        }
        if not path.endswith(self.__FILE_EXT):
            path = path + '.' + self.__FILE_EXT
        with open(path, 'w') as file:
            json.dump(session_object, file, indent=2)

    def get_name(self):
        return self.__NAME

    def get_url(self):
        return self.__URL

    def get_file_ext(self):
        return self.__FILE_EXT

    # TODO: Remove driver dependency
    def get_idb_db_names(self, driver):
        return []
