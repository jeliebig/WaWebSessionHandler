from typing import NoReturn, Optional, ValuesView


class IDBObjectStore:
    name: str
    auto_increment: bool
    key_path: str
    __indices: dict[str, bool]
    __data: list[dict[str, str]]

    def __is_unique_value(self, index: str, value: Optional[str]) -> bool:
        for entry in self.__data:
            if value == entry[index]:
                return False
        return True

    # It's possible to pass an array to keyPath, but since I don't know how that gets handled
    # only strings can be used for now.
    def __init__(self, name: str, auto_increment: Optional[bool] = False, key_path: Optional[str] = ""):
        self.name = name.strip()
        self.auto_increment = auto_increment
        self.key_path = key_path.strip()
        if len(key_path.strip()) > 0:
            self.__indices[key_path.strip()] = True

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
            else:
                raise ValueError(f'No such index in ObjectStore: {index}')
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

    def __init__(self, name: str, version: Optional[int] = 1):
        self.name = name.strip()
        if version > 0:
            self.version = version
        else:
            raise ValueError('Version cannot be <= 0')

    def add_object_store(self, object_store: IDBObjectStore) -> NoReturn:
        if object_store.name not in self.__object_stores.keys():
            self.__object_stores[object_store.name] = object_store
        else:
            raise ValueError(f'Cannot add object store. Duplicate name: {object_store.name}')

    def get_object_store_num(self):
        return len(self.__object_stores)

    def get_object_stores(self) -> ValuesView[IDBObjectStore]:
        return self.__object_stores.values()


class IndexedDB:
    url: str
    __databases: dict[str, IDBDatabase]

    def __init__(self, url: str):
        self.url = url.strip()

    def add_db(self, db: IDBDatabase) -> NoReturn:
        if db.name not in self.__databases.keys():
            self.__databases[db.name] = db
        else:
            raise ValueError(f'Cannot add db. Duplicate name: {db.name}')

    def get_db_num(self):
        return len(self.__databases)

    def get_dbs(self) -> ValuesView[IDBDatabase]:
        return self.__databases.values()

    def get_db(self, name: str) -> IDBDatabase:
        return self.__databases[name]


class SessionObject:
    url: str
    cookies: dict[str, str]
    local_storage: dict[str, str]
    indexed_db: IndexedDB

    def __init__(self, url: str,
                 cookies: Optional[dict[str, str]] = None,
                 local_storage: Optional[dict[str, str]] = None,
                 indexed_db: Optional[IndexedDB] = None):
        self.url = url.strip()
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
            self.indexed_db = IndexedDB(self.url)
