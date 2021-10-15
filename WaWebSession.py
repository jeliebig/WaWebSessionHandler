#!/usr/bin/env python3
import json
import logging
import os
import platform
import time
from enum import Enum
from typing import Union, NoReturn, Optional

import selenium.webdriver.chrome.options as c_op
import selenium.webdriver.chrome.webdriver as c_wd
import selenium.webdriver.firefox.options as f_op
import selenium.webdriver.firefox.webdriver as f_wd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class Browser(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"


class SessionHandler:
    __URL = 'https://web.whatsapp.com/'
    __browser_choice = 0
    __browser_user_dir: str
    __browser_profile_list: 'list[str]'
    __browser_options: Union[c_op.Options, f_op.Options]
    __driver: Union[c_wd.WebDriver, f_wd.WebDriver] = None
    __custom_driver = False
    __log: logging.Logger

    @staticmethod
    def verify_profile_object(profile_obj: Union['list[dict[str, str]]', 'list[str]']) -> bool:
        for entry in profile_obj:
            if isinstance(entry, str):
                if 'WASecretBundle' in entry or 'logout-token' in entry:
                    return True
            elif isinstance(entry, dict):
                if 'key' in entry.keys() and ('WASecretBundle' in entry['key'] or 'logout-token' in entry['key']):
                    return True
            else:
                raise TypeError
        return False

    @staticmethod
    def convert_ls_to_idb_obj(ls_obj: 'dict[str, str]') -> 'list[dict[str, str]]':
        idb_list = []
        for ls_key, ls_val in ls_obj.items():
            idb_list.append({'key': ls_key, 'value': ls_val})
        return idb_list

    @staticmethod
    def convert_idb_to_ls_obj(idb_obj: 'list[dict[str, str]]') -> 'dict[str, str]':
        ls_dict = {}
        for idb_entry in idb_obj:
            ls_dict[idb_entry['key']] = idb_entry['value']
        return ls_dict

    @staticmethod
    def get_newer_obj_from_ls_cmp(load_ls_obj: 'dict[str, str]', first_cmp_obj: 'dict[str, str]',
                                  second_cmp_obj: 'dict[str, str]') -> 'dict[str, str]':
        for ls_key, ls_val in load_ls_obj.items():
            # TODO: does this still result in the behavior we want?
            if ls_key not in first_cmp_obj.keys() or ls_key not in second_cmp_obj.keys():
                continue
            # check if the value really changed
            if first_cmp_obj[ls_key] != second_cmp_obj[ls_key]:
                # using two ifs in case they really change both values at some point
                if first_cmp_obj[ls_key] != ls_val:
                    return first_cmp_obj
                if second_cmp_obj[ls_key] != ls_val:
                    return second_cmp_obj
        return load_ls_obj

    def __refresh_profile_list(self) -> NoReturn:
        if not self.__custom_driver:
            if os.path.isdir(self.__browser_user_dir):
                self.__log.debug('Getting browser profiles...')
                if self.__browser_choice == Browser.CHROME:
                    self.__browser_profile_list = ['']
                    for profile_dir in os.listdir(self.__browser_user_dir):
                        if 'profile' in profile_dir.lower():
                            if profile_dir != 'System Profile':
                                self.__browser_profile_list.append(profile_dir)
                elif self.__browser_choice == Browser.FIREFOX:
                    # TODO: consider reading out the profiles.ini
                    self.__browser_profile_list = []
                    for profile_dir in os.listdir(self.__browser_user_dir):
                        if not profile_dir.endswith('.default'):
                            if os.path.isdir(os.path.join(self.__browser_user_dir, profile_dir)):
                                self.__browser_profile_list.append(profile_dir)

                self.__log.debug('Browser profiles registered.')
            else:
                self.__log.error('Browser user dir does not exist.')
                self.__browser_profile_list = []
        else:
            # TODO: Figure out why I did that before
            raise AssertionError('Do not call this method while using a custom driver.')

    def __init_browser(self) -> NoReturn:
        self.__custom_driver = False
        self.__log.debug("Setting browser user dirs...")
        if self.__browser_choice == Browser.CHROME:
            self.__browser_options = webdriver.ChromeOptions()

            if self.__platform == 'windows':
                self.__browser_user_dir = os.path.join(os.environ['USERPROFILE'],
                                                       'Appdata', 'Local', 'Google', 'Chrome', 'User Data')
            elif self.__platform == 'linux':
                self.__browser_user_dir = os.path.join(os.environ['HOME'], '.config', 'google-chrome')

        elif self.__browser_choice == Browser.FIREFOX:
            self.__browser_options = webdriver.FirefoxOptions()

            if self.__platform == 'windows':
                self.__browser_user_dir = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
                self.__browser_profile_list = os.listdir(self.__browser_user_dir)
            elif self.__platform == 'linux':
                self.__browser_user_dir = os.path.join(os.environ['HOME'], '.mozilla', 'firefox')

        self.__log.debug('Browser user dirs set.')

        self.__browser_options.headless = True
        self.__refresh_profile_list()

    def __get_local_storage(self) -> 'dict[str, str]':
        self.__log.debug('Executing getLS function...')
        return self.__driver.execute_script('''
        var waSession = {};
        waLs = window.localStorage;
        for (var i = 0; i < waLs.length; i++) {
            waSession[waLs.key(i)] = waLs.getItem(waLs.key(i));
        }
        return waSession;
        ''')

    def __set_local_storage(self, wa_session_obj: 'dict[str, str]') -> NoReturn:
        for ls_key, ls_val in wa_session_obj.items():
            self.__driver.execute_script('window.localStorage.setItem(arguments[0], arguments[1]);',
                                         ls_key, ls_val)

    def __get_indexed_db_user(self) -> 'list[dict[str, str]]':
        self.__log.debug('Executing getIDBObjects function...')
        self.__driver.execute_script('''
        document.waScript = {};
        document.waScript.waSession = undefined;
        function getAllObjects() {
            document.waScript.dbName = "wawc";
            document.waScript.osName = "user";
            document.waScript.db = undefined;
            document.waScript.transaction = undefined;
            document.waScript.objectStore = undefined;
            document.waScript.getAllRequest = undefined;
            document.waScript.request = indexedDB.open(document.waScript.dbName);
            document.waScript.request.onsuccess = function(event) {
                document.waScript.db = event.target.result;
                document.waScript.transaction = document.waScript.db.transaction(document.waScript.osName);
                document.waScript.objectStore = document.waScript.transaction.objectStore(document.waScript.osName);
                document.waScript.getAllRequest = document.waScript.objectStore.getAll();
                document.waScript.getAllRequest.onsuccess = function(getAllEvent) {
                    document.waScript.waSession = getAllEvent.target.result;
                };
            };
        }
        getAllObjects();
        ''')
        self.__log.debug('Waiting until IDB operation finished...')
        while not self.__driver.execute_script('return document.waScript.waSession != undefined;'):
            time.sleep(1)
        self.__log.debug('Getting IDB results...')
        wa_session_obj: list[dict[str, str]] = self.__driver.execute_script('return document.waScript.waSession;')
        # self.__log.debug('Got IDB data: %s', wa_session_obj)
        return wa_session_obj

    def __set_indexed_db_user(self, wa_session_obj: 'list[dict[str, str]]') -> NoReturn:
        self.__log.debug('Inserting setIDBObjects function...')
        self.__driver.execute_script('''
        document.waScript = {};
        document.waScript.insertDone = 0;
        document.waScript.jsonObj = undefined;
        document.waScript.setAllObjects = function (_jsonObj) {
            document.waScript.jsonObj = _jsonObj;
            document.waScript.dbName = "wawc";
            document.waScript.osName = "user";
            document.waScript.db;
            document.waScript.transaction;
            document.waScript.objectStore;
            document.waScript.clearRequest;
            document.waScript.addRequest;
            document.waScript.request = indexedDB.open(document.waScript.dbName);
            document.waScript.request.onsuccess = function(event) {
                document.waScript.db = event.target.result;
                document.waScript.transaction = document.waScript.db.transaction(document.waScript.osName, "readwrite");
                document.waScript.objectStore = document.waScript.transaction.objectStore(document.waScript.osName);
                document.waScript.clearRequest = document.waScript.objectStore.clear();
                document.waScript.clearRequest.onsuccess = function(clearEvent) {
                    for (var i = 0; i < document.waScript.jsonObj.length; i++) {
                        document.waScript.addRequest = document.waScript.objectStore.add(document.waScript.jsonObj[i]);
                        document.waScript.addRequest.onsuccess = function(addEvent) {
                            document.waScript.insertDone++;
                        };
                    }
                };
            };
        }
        ''')
        self.__log.debug('setIDBObjects function inserted.')

        self.__log.info('Writing IDB data...')
        self.__driver.execute_script('document.waScript.setAllObjects(arguments[0]);', wa_session_obj)

        self.__log.debug('Waiting until all objects are written to IDB...')
        # FIXME: This looks awful. Please find a way to make this look a little better.
        while not self.__driver.execute_script(
                'return (document.waScript.insertDone == document.waScript.jsonObj.length);'):
            time.sleep(1)

    def __verify_profile_name_exists(self, profile_name: str) -> bool:
        if self.__custom_driver:
            raise AssertionError('Do not call this method if you are using a custom webdriver.')
        # NOTE: Is this still required?
        if not isinstance(profile_name, str):
            raise TypeError('The provided profile_name is not a string.')

        return True if profile_name in self.__browser_profile_list else False

    def __start_session(self, options: Optional[Union[c_op.Options, f_op.Options]] = None,
                        profile_name: Optional[str] = None, wait_for_login=True) -> NoReturn:
        if not self.__custom_driver and options is None:
            raise ValueError("Do not call this method without providing options for the webdriver.")
        if profile_name is None:
            if not self.__custom_driver:
                self.__log.info('Starting browser... [HEADLESS: %s]', str(options.headless))
                if self.__browser_choice == Browser.CHROME:
                    self.__driver = webdriver.Chrome(options=options)
                elif self.__browser_choice == Browser.FIREFOX:
                    self.__driver = webdriver.Firefox(options=options)
            else:
                self.__log.debug('Checking if current browser window can be used...')
                if self.__browser_choice == Browser.CHROME:
                    if self.__driver.current_url != 'chrome://new-tab-page/' and self.__driver.current_url != 'data:,':
                        self.__driver.execute_script('window.open()')
                        self.__driver.switch_to.window(self.__driver.window_handles[-1])
                elif self.__browser_choice == Browser.FIREFOX:
                    if self.__driver.current_url != "about:blank":
                        self.__driver.execute_script('window.open()')
                        self.__driver.switch_to.window(self.__driver.window_handles[-1])

            self.__log.info('Loading WhatsApp Web...')
            self.__driver.get(self.__URL)

            if wait_for_login:
                timeout = 120
                login_success = True
                self.__log.info('Waiting for login... [Timeout: %ss]', timeout)
                while not self.verify_profile_object(self.__get_indexed_db_user()):
                    time.sleep(1)
                    timeout -= 1
                    if timeout == 0:
                        login_success = False
                        break
                if not login_success:
                    self.__log.error('Login was not completed in time. Aborting...')
                    return
                self.__log.info('Login completed.')
        else:
            self.__log.info('Starting browser... [HEADLESS: %s]', str(options.headless))
            if self.__browser_choice == Browser.CHROME:
                options.add_argument('user-data-dir=%s' % os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Chrome(options=options)
            elif self.__browser_choice == Browser.FIREFOX:
                fire_profile = webdriver.FirefoxProfile(os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Firefox(fire_profile, options=options)

            self.__log.info('Loading WhatsApp Web...')
            self.__driver.get(self.__URL)

    def __start_visible_session(self, profile_name: Optional[str] = None, wait_for_login=True) -> NoReturn:
        options = self.__browser_options
        options.headless = False

        if profile_name is not None:
            self.__verify_profile_name_exists(profile_name)
        self.__start_session(options, profile_name, wait_for_login)

    def __start_invisible_session(self, profile_name: Optional[str] = None) -> NoReturn:
        if profile_name is not None:
            self.__verify_profile_name_exists(profile_name)
        self.__start_session(self.__browser_options, profile_name)

    def __get_profile_storage(self, profile_name: Optional[str] = None) -> 'list[dict[str, str]]':
        if profile_name is None:
            if self.__custom_driver:
                self.__start_session()
            else:
                self.__start_visible_session()
        else:
            self.__start_invisible_session(profile_name)

        indexed_db = self.__get_indexed_db_user()

        if not self.__custom_driver:
            self.__log.info("Closing browser...")
            self.__driver.quit()
        else:
            self.__log.info("Closing tab...")
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[-1])

        return indexed_db

    def __init__(self, browser: Optional[Union[Browser, str]] = None,
                 driver: Optional[Union[c_wd.WebDriver, f_wd.WebDriver]] = None):
        self.__log = logging.getLogger('WaWebSession')
        self.__log.setLevel(logging.DEBUG)

        self.__platform = platform.system().lower()
        if self.__platform != 'windows' and self.__platform != 'linux':
            raise NotImplementedError('Only Windows and Linux are supported for now.')
        self.__log.debug('Detected platform: %s', self.__platform)

        if driver:
            self.set_custom_webdriver(driver)
        else:
            if browser:
                self.set_browser(browser)
            else:
                raise ValueError('Parameter browser is empty.\n'
                                 'You need to set a browser or a custom driver during object creation.')

            self.__init_browser()

    def set_custom_webdriver(self, driver: Union[c_wd.WebDriver, f_wd.WebDriver]) -> NoReturn:
        if isinstance(driver, c_wd.WebDriver):
            self.__browser_choice = Browser.CHROME
        elif isinstance(driver, f_wd.WebDriver):
            self.__browser_choice = Browser.FIREFOX
        self.__custom_driver = True
        self.__driver = driver

    def set_browser(self, browser: Union[Browser, str]) -> NoReturn:
        if self.__driver is not None:
            self.__driver.quit()

        if isinstance(browser, str):
            if browser.lower() == 'chrome':
                self.__log.debug('Setting browser... [TYPE: %s]', 'Chrome')
                self.__browser_choice = Browser.CHROME
            elif browser.lower() == 'firefox':
                self.__log.debug('Setting browser... [TYPE: %s]', 'Firefox')
                self.__browser_choice = Browser.FIREFOX
            else:
                raise ValueError('The specified browser is invalid. Try to use "chrome" or "firefox" instead.')
        elif isinstance(browser, Browser):
            if browser == Browser.CHROME:
                self.__log.debug('Setting browser... [TYPE: %s]', 'Chrome')
            elif browser == Browser.FIREFOX:
                self.__log.debug('Setting browser... [TYPE: %s]', 'Firefox')
            self.__browser_choice = browser
        else:
            # NOTE: This shouldn't be needed anymore.
            raise TypeError(
                'Type of browser invalid. Please use Browser.CHROME or Browser.FIREFOX instead.'
            )
        self.__init_browser()

    # TODO: Think about type aliasing
    def get_active_session(self, use_profile: Optional[Union['list[str]', str]] = None, all_profiles=False) -> Union[
        'list[dict[str, str]]', 'dict[str, list[dict[str, str]]]'
    ]:
        self.__log.info('Make sure the specified browser profile is not being used by another process.')
        profile_storage_dict = {}
        use_profile_list = []
        self.__refresh_profile_list()

        if self.__custom_driver:
            raise AssertionError('Do not call this method if you are using a custom webdriver.')

        if all_profiles:
            use_profile_list.extend(self.__browser_profile_list)
            self.__log.info(
                'Trying to get active sessions for all browser profiles of the selected type...'
            )
        else:
            if use_profile and use_profile not in self.__browser_profile_list:
                raise ValueError('Profile does not exist: %s', use_profile)
            elif use_profile is None:
                return self.__get_profile_storage()
            elif use_profile and use_profile in self.__browser_profile_list:
                use_profile_list.append(use_profile)
            elif isinstance(use_profile, list):
                use_profile_list.extend(use_profile)
            else:
                raise ValueError(
                    'Invalid profile provided. Make sure you provided a list of profiles or a profile name.'
                )

        for profile in use_profile_list:
            profile_storage_dict[profile] = self.__get_profile_storage(profile)

        return profile_storage_dict

    def create_new_session(self) -> 'list[dict[str, str]]':
        return self.__get_profile_storage()

    def access_by_obj(self, wa_profile_obj: 'list[dict[str, str]]') -> 'list[dict[str, str]]':
        if not self.verify_profile_object(wa_profile_obj):
            raise TypeError(
                'Invalid profile object provided. '
                'Make sure you only pass one session to this method.'
            )

        if not self.__custom_driver:
            self.__start_visible_session(wait_for_login=False)
        else:
            self.__start_session(wait_for_login=False)

        self.__set_indexed_db_user(wa_profile_obj)
        self.__set_local_storage(self.convert_idb_to_ls_obj(wa_profile_obj))
        self.__log.info('Reloading WhatsApp Web...')
        self.__driver.refresh()
        self.__log.debug('Waiting until WhatsApp Web finished loading...')
        wait = WebDriverWait(self.__driver, 60)
        wait.until(
            ec.visibility_of_element_located((By.XPATH, '/html/body/div/div[1]/div[1]/div[4]/div/div/div[2]/h1'))
        )
        self.__log.info('WhatsApp Web is now usable!')
        return_idb_obj = self.convert_ls_to_idb_obj(self.get_newer_obj_from_ls_cmp(
            self.convert_idb_to_ls_obj(wa_profile_obj),
            self.__get_local_storage(),
            self.convert_idb_to_ls_obj(self.__get_indexed_db_user()))
        )

        if not self.__custom_driver:
            self.__log.info('Do not reload the page manually.')
            self.__log.info('Waiting until the browser window is closed...')
            while True:
                try:
                    _ = self.__driver.current_window_handle
                    time.sleep(1)
                except WebDriverException:
                    break
        return return_idb_obj

    def access_by_file(self, profile_file: str) -> NoReturn:
        profile_file = os.path.normpath(profile_file)

        if os.path.isfile(profile_file):
            self.__log.debug('Reading WaSession from file...')
            with open(profile_file, 'r') as file:
                wa_profile_obj = json.load(file)

            self.__log.debug('Verifying WaSession object...')
            if not self.verify_profile_object(wa_profile_obj):
                raise TypeError(
                    'There might be multiple profiles stored in this file. '
                    'Make sure you only pass one WaSession file to this method.'
                )

            self.__log.info('WaSession object is valid.')
            new_wa_profile_obj = self.access_by_obj(wa_profile_obj)
            self.save_profile(new_wa_profile_obj, profile_file)

        else:
            raise FileNotFoundError('Make sure you pass a valid WaSession file to this method.')

    def save_profile(self, wa_profile_obj: Union['list[dict[str, str]]', 'dict[str, list[dict[str, str]]]'],
                     file_path: str) -> Union[NoReturn, int]:
        file_path = os.path.normpath(file_path)

        if self.verify_profile_object(wa_profile_obj):
            self.__log.info('Saving WaSession object to file...')
            with open(file_path, 'w') as file:
                json.dump(wa_profile_obj, file, indent=2)
        else:
            if isinstance(wa_profile_obj, dict):
                self.__log.info('Scanning the list for multiple WaSession objects...')
                if len(wa_profile_obj) == 0:
                    raise ValueError(
                        'Could not find any profiles in the list. Make sure to specified file path is correct.'
                    )

                saved_profiles = 0
                for profile_name in wa_profile_obj.keys():
                    profile_storage = wa_profile_obj[profile_name]
                    if self.verify_profile_object(profile_storage):
                        self.__log.info('Found a new profile in the list!')
                        single_profile_name = os.path.basename(file_path) + '-' + profile_name
                        self.save_profile(profile_storage,
                                          os.path.join(os.path.dirname(file_path), single_profile_name))
                        saved_profiles += 1
                if saved_profiles > 0:
                    if saved_profiles > 1:
                        self.__log.info('Saved %s profile objects as files.', saved_profiles)
                    else:
                        self.__log.info('Saved %s profile object as file.', saved_profiles)
                else:
                    self.__log.error("Could not find any active profiles in the list.")
                return saved_profiles
            else:
                return ValueError('WaSession object is not valid.')


if __name__ == '__main__':
    log_format = logging.Formatter('%(asctime)s [%(levelname)s] (%(funcName)s): %(message)s')
    log_stream = logging.StreamHandler()
    log_stream.setLevel(logging.INFO)
    log_stream.setFormatter(log_format)
    logging.getLogger('WaWebSession').addHandler(log_stream)
    log_file = logging.FileHandler('WaWebSession.log')
    log_file.setLevel(logging.DEBUG)
    log_file.setFormatter(log_format)
    logging.getLogger('WaWebSession').addHandler(log_file)

    web = None
    input_browser_choice = 0
    while input_browser_choice != 1 and input_browser_choice != 2:
        print('1) Chrome\n'
              '2) Firefox\n')
        input_browser_choice = int(input('Select a browser by choosing a number from the list: '))
    if input_browser_choice == 1:
        web = SessionHandler(Browser.CHROME)
    elif input_browser_choice == 2:
        web = SessionHandler(Browser.FIREFOX)

    choice = 0
    while choice != 1 and choice != 2 and choice != 3:
        print('1) Save a new session as a file\n'
              '2) Save all active sessions for the selected browser to files\n'
              '3) Open a session from a file\n')
        choice = int(input('Select an option from the list: '))
    if choice == 1:
        waSession = web.get_active_session()
        if web.verify_profile_object(waSession):
            web.save_profile(waSession, input('Enter a file path for the created session file: '))
            print('File successfully created.')
    elif choice == 2:
        waSessions = web.get_active_session(all_profiles=True)
        if len(waSessions) > 0:
            verified_profiles = 0
            for waProfile in waSessions.keys():
                if web.verify_profile_object(waSessions[waProfile]):
                    verified_profiles += 1
            if verified_profiles == 0:
                print("No active sessions found. Exiting...")
                exit(1)
        else:
            print("No active sessions found. Exiting...")
            exit(1)
        created_files = web.save_profile(waSessions,
                                         input('Enter a file path for the created session files: '))
        if created_files > 0:
            print('Files successfully created.')
    elif choice == 3:
        web.access_by_file(input('Enter the file path to the session file you would like to open: '))
