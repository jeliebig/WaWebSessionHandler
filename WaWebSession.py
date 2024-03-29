#!/usr/bin/env python3
import logging
import os
from typing import NoReturn, Optional

import version
from SessionHandler import *


class WaWebSession(SessionObject):
    __version: version.Version
    __log: logging.Logger

    @staticmethod
    def create_from_file(path: str):
        # FIXME: I should probably use __init__ for these things and not a static method
        new_waso = SessionObject.create_from_file(path)
        new_waso.__class__ = WaWebSession
        new_waso.update_version()
        new_waso.update_logger()
        return new_waso

    @staticmethod
    def is_valid_session(cookies: dict[str, str],
                         local_storage: dict[str, str],
                         indexed_db: IndexedDB):
        tmp_waso = WaWebSession(cookies, local_storage, indexed_db)
        if version.is_any_version(tmp_waso):
            return tmp_waso
        else:
            return None

    def __init__(self, cookies: Optional[dict[str, str]] = None,
                 local_storage: Optional[dict[str, str]] = None,
                 indexed_db: Optional[IndexedDB] = None):
        # waso: WhatsApp (Web) Session Object
        super().__init__('WhatsApp Web', 'https://web.whatsapp.com/', 'waso', cookies, local_storage, indexed_db)
        self.idb_special_treatment = False

        self.__log = logging.getLogger('SessionHandler')

        if cookies is not None and local_storage is not None and indexed_db is not None:
            self.__version = version.get_version(self)
            if self.__version is None:
                raise ValueError('WhatsApp Web version could not be identified.\n'
                                 'Please check if the SessionObject is valid.')

    def update_logger(self, name='SessionHandler') -> NoReturn:
        self.__log = logging.getLogger(name)

    def get_version(self) -> version.Version:
        return self.__version

    def update_version(self) -> NoReturn:
        self.__version = version.get_version(self)

    def update_session(self, cookies: dict[str, str],
                       local_storage: dict[str, str],
                       indexed_db: IndexedDB) -> NoReturn:
        self.cookies = cookies
        self.local_storage = local_storage
        self.indexed_db = indexed_db

    def get_idb_db_names(self) -> list:
        # FIXME: wawc_db_enc CryptoKeys do not get dumped correctly
        return ["wawc", "wawc_db_enc", "signal-storage", "model-storage"]

    def get_idb_st_layout(self) -> dict[str, list[str]]:
        raise NotImplementedError

    def do_idb_st_get_action(self, driver) -> dict[str, object]:
        raise NotImplementedError

    def do_idb_st_set_action(self, driver, data: dict[str, dict[str, list[dict[str, object]]]]):
        raise NotImplementedError


if __name__ == '__main__':
    sh_logger = logging.getLogger('SessionHandler')
    log_format = logging.Formatter('%(asctime)s [%(levelname)s] (%(funcName)s): %(message)s')
    log_stream = logging.StreamHandler()
    log_stream.setLevel(logging.INFO)
    log_stream.setFormatter(log_format)
    sh_logger.addHandler(log_stream)
    log_file = logging.FileHandler('SessionHandler.log')
    log_file.setLevel(logging.DEBUG)
    log_file.setFormatter(log_format)
    sh_logger.addHandler(log_file)

    web = None
    input_browser_choice = 0
    while input_browser_choice != 1 and input_browser_choice != 2:
        print('1) Chrome\n'
              '2) Firefox\n')
        input_browser_choice = int(input('Select a browser by choosing a number from the list: '))

    choice = 0
    while choice != 1 and choice != 2 and choice != 3:
        print('1) Save a new session as a file\n'
              '2) Save all active sessions for the selected browser to files\n'
              '3) Open a session from a file\n')
        choice = int(input('Select an option from the list: '))

    if choice == 1 or choice == 2:
        if input_browser_choice == 1:
            web = SessionHandler(WaWebSession(), Browser.CHROME)
        elif input_browser_choice == 2:
            web = SessionHandler(WaWebSession(), Browser.FIREFOX)
    if choice == 1:
        waSession = web.create_new_session()
        save_path = input('Enter a file path for the created session file: ')
        waSession.save_to_file(save_path)
        sh_logger.info(f'Saved session to file: {save_path + "." + waSession.get_file_ext()}')
    elif choice == 2:
        waSessions = web.get_active_session(all_profiles=True)
        if len(waSessions) == 0:
            sh_logger.error('No active sessions found. Exiting...')
            exit(1)
        save_path = input('Enter a file path for the created session files: ')
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        for browser_profile, waSession in waSessions.items():
            sh_logger.info(f"Saving '{browser_profile}' to '{save_path}'...")
            waSession.save_to_file(os.path.join(save_path, browser_profile))
        sh_logger.info('Successfully saved all sessions!')
    elif choice == 3:
        file_path = input('Enter the file path to the session file you would like to open: ')
        waSession = WaWebSession.create_from_file(file_path)
        if input_browser_choice == 1:
            web = SessionHandler(waSession, Browser.CHROME)
        elif input_browser_choice == 2:
            web = SessionHandler(waSession, Browser.FIREFOX)

        new_waSession = web.open_session()
        sh_logger.info('Saving closed session...')
        new_waSession.save_to_file(file_path)
        sh_logger.info('Successfully saved session to file!')
