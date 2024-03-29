import logging
import os
import platform
import time
from enum import Enum
from typing import NoReturn, Union, Optional

import selenium.webdriver.chrome.options as c_op
import selenium.webdriver.chrome.webdriver as c_wd
import selenium.webdriver.firefox.options as f_op
import selenium.webdriver.firefox.webdriver as f_wd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from SessionHandler.SessionObject import SessionObject, IndexedDB


class Browser(Enum):
    CHROME = 'chrome'
    FIREFOX = 'firefox'


class SessionHandler:
    __browser_choice = 0
    __browser_options: Union[c_op.Options, f_op.Options]
    __browser_profile_list: 'list[str]'
    __browser_user_dir: str
    __custom_driver = False
    __driver: Union[c_wd.WebDriver, f_wd.WebDriver] = None
    __log: logging.Logger
    __session: SessionObject

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
        self.__log.debug('Setting browser user dirs...')
        if self.__browser_choice == Browser.CHROME:
            self.__browser_options = webdriver.ChromeOptions()
            if self.__platform == 'windows':
                self.__browser_user_dir = os.path.join(
                    os.environ['USERPROFILE'], 'Appdata', 'Local', 'Google', 'Chrome', 'User Data')
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

    def __get_cookies(self) -> dict:
        self.__log.debug('Executing getCookies function...')
        cookie_list = self.__driver.execute_script('''
        return document.cookie.split("; ");
        ''')
        cookie_dict = {}
        for cookie in cookie_list:
            if len(cookie) == 0:
                continue
            cookie = cookie.split("=", maxsplit=1)
            cookie_dict[cookie[0]] = cookie[1]
        return cookie_dict

    def __set_cookies(self, cookie_dict: dict[str, str]) -> NoReturn:
        cookie_string = ""
        for key, value in cookie_dict.items():
            cookie_string += f"{key}={value}; "
        self.__driver.execute_script('''
        document.cookie = arguments[0];
        ''', cookie_string)

    def __get_local_storage(self) -> 'dict[str, str]':
        self.__log.debug('Executing getLocalStorage function...')
        return self.__driver.execute_script('''
        var localStorageDict = {};
        var ls = window.localStorage;
        for (var i = 0; i < ls.length; i++) {
            localStorageDict[ls.key(i)] = ls.getItem(ls.key(i));
        }
        return localStorageDict;
        ''')

    def __set_local_storage(self, local_storage_dict: 'dict[str, str]') -> NoReturn:
        for ls_key, ls_val in local_storage_dict.items():
            self.__driver.execute_script('window.localStorage.setItem(arguments[0], arguments[1]);',
                                         ls_key, ls_val)

    def __get_indexed_db(self) -> IndexedDB:
        idb_dict = {'url': self.__session.get_url(), 'databases': {}}
        idb_db_names = self.__session.get_idb_db_names(self.__driver)
        if self.__session.idb_special_treatment:
            self.__log.info("IDB special treatment required.")
            idb_st_layout = self.__session.get_idb_st_layout()
        else:
            idb_st_layout = None
        self.__log.debug('Executing getIndexedDb function...')
        # FIXME: Use driver.execute_async_script() in the future
        self.__driver.execute_script('''
        document.pySessionHandler = {};
        document.pySessionHandler.idbObject = {};
        document.pySessionHandler.idbReady = 0;
        document.pySessionHandler.idbNames = arguments[0];
        document.pySessionHandler.idbStLayout = arguments[1];
        // This could be so easy
        // https://developer.mozilla.org/en-US/docs/Web/API/IDBFactory/databases#browser_compatibility
        // indexedDB.databases();
        async function getAllIndexedDBs() {
          for (const dbName of document.pySessionHandler.idbNames) {
            document.pySessionHandler.idbObject[dbName] = {};
            document.pySessionHandler.db = await new Promise((resolve, reject) => {
              document.pySessionHandler.openRequest = indexedDB.open(dbName);
              document.pySessionHandler.openRequest.onsuccess = _ => resolve(
                document.pySessionHandler.openRequest.result
              );
            });
            document.pySessionHandler.idbObject[dbName]['name'] = document.pySessionHandler.db.name;
            document.pySessionHandler.idbObject[dbName]['version'] = document.pySessionHandler.db.version;
            document.pySessionHandler.idbObject[dbName]['objectStores'] = {};
            for (const objectStoreName of document.pySessionHandler.db.objectStoreNames) {
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName] = {};
              document.pySessionHandler.osTransaction = document.pySessionHandler.db.transaction(
                objectStoreName
              );
              document.pySessionHandler.objectStore = document.pySessionHandler.osTransaction.objectStore(
                objectStoreName
              );
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName] = {};
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName]['name'] =
                objectStoreName;
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName]['indices'] = {};
              for (const idbIndexName of Array.from(document.pySessionHandler.objectStore.indexNames)) {
                idbIndex = document.pySessionHandler.objectStore.index(idbIndexName);
                document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName]['indices'][
                  idbIndex.name
                ] = {'unique': idbIndex.unique, 'keyPath': idbIndex.keyPath, 'multiEntry': idbIndex.multiEntry};
              }
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName]['keyPath'] =
                document.pySessionHandler.objectStore.keyPath;
              document.pySessionHandler.idbObject[dbName]['objectStores'][objectStoreName]['autoIncrement'] =
                document.pySessionHandler.objectStore.autoIncrement;
              document.pySessionHandler.osName = objectStoreName;
              if (document.pySessionHandler.idbStLayout != null &&
                document.pySessionHandler.idbStLayout[dbName] != undefined &&
                document.pySessionHandler.idbStLayout[dbName][document.pySessionHandler.osName] != undefined) {
                    document.pySessionHandler.idbObject[dbName]['objectStores'][document.pySessionHandler.osName]['data']
                     = []; 
              }
              else {
                document.pySessionHandler.idbObject[dbName]['objectStores'][document.pySessionHandler.osName]['data']
                 = await new Promise((resolve, reject) => {
                    document.pySessionHandler.osGetAllRequest = document.pySessionHandler.objectStore.getAll();
                    document.pySessionHandler.osGetAllRequest.onsuccess =
                      _ => resolve(document.pySessionHandler.osGetAllRequest.result);
                });
              }
            }
            document.pySessionHandler.db.close();
            document.pySessionHandler.idbReady++;
          }
        }
        getAllIndexedDBs();
        ''', idb_db_names, idb_st_layout)
        self.__log.debug('Waiting until IDB operation is done...')
        while not self.__driver.execute_script(
                f'return document.pySessionHandler.idbReady == {len(idb_db_names)};'):
            time.sleep(1)
        self.__log.debug('Getting IDB results...')
        idb_dict['databases'] = self.__driver.execute_script(
            'return document.pySessionHandler.idbObject;')
        self.__driver.execute_script('document.pySessionHandler = {};')
        if idb_st_layout is not None:
            self.__log.info("Running special actions...")
            st_data = self.__session.do_idb_st_get_action(self.__driver)
            for idb_st_db, idb_st_os_list in idb_st_layout.items():
                for idb_st_os in idb_st_os_list:
                    idb_dict['databases'][idb_st_db]['objectStores'][idb_st_os]['data'] = st_data[idb_st_db][idb_st_os]
        return IndexedDB.create_from_dict(idb_dict)

    def __set_indexed_db(self, idb: IndexedDB) -> NoReturn:
        self.__log.debug('Inserting setIDBObjects function...')
        self.__driver.execute_script('''
        document.pySessionHandler = {};
        // Reference PoC: https://github.com/jeliebig/WaWebSessionHandler/issues/15#issuecomment-893716129
        // PoC by: https://github.com/thewh1teagle
        document.pySessionHandler.setAllObjects = async function (idb_data, stLayout) {
            idb_dbs = idb_data['databases'];
            for (const [idbDbName, idbDbProps] of Object.entries(idb_dbs)) {
                await new Promise((resolve, reject) => {
                    deleteRequest = indexedDB.deleteDatabase(idbDbName);
                    deleteRequest.onsuccess = _ => resolve(_);
                    deleteRequest.onerror = _ => resolve(_);
                });
                await new Promise((resolve, reject) => {
                    openRequest = indexedDB.open(idbDbName, idbDbProps['version']);
                    openRequest.onupgradeneeded = async function(event) {
                        db = event.target.result;
                        
                        for (const [idbOsName, idbOsProps] of Object.entries(idbDbProps['objectStores'])) {
                            console.log("OS:", idbOsName, idbOsProps);
                            objectStoreOptions = {
                              autoIncrement: idbOsProps['autoIncrement']
                            };
                            if (idbOsProps['keyPath'].length > 0){
                               objectStoreOptions['keyPath'] = (idbOsProps['keyPath'].length == 1 ?
                                idbOsProps['keyPath'].join('') : idbOsProps['keyPath']);
                            }
                            objectStore = db.createObjectStore(idbOsName, objectStoreOptions);
                            containsUniqueIndex = false; 
                            for (const [idbIndexName, idbIndexOptions] of Object.entries(idbOsProps['indices'])) {
                                if (idbIndexOptions['unique']) {
                                    containsUniqueIndex = true;
                                } 
                                objectStore.createIndex(idbIndexName, idbIndexOptions['keyPath'],{
                                    unique: idbIndexOptions['unique'],
                                    multiEntry: idbIndexOptions['multiEntry']
                                });    
                            }
                            if (!(stLayout != null &&
                             stLayout[idbDbName] != undefined && stLayout[idbDbName][idbOsName] != undefined)) {
                                i = 1;
                                for (const idbOsData of idbOsProps['data']) {
                                    if (containsUniqueIndex || idbOsProps['keyPath'].length > 0) {
                                        await new Promise((dResolve, dReject) => {
                                            addRequest = objectStore.add(idbOsData);
                                            addRequest.onsuccess = _ => dResolve();
                                        });
                                    }
                                    else {
                                        await new Promise((dResolve, dReject) => {
                                            addRequest = objectStore.add(idbOsData, i);
                                            addRequest.onsuccess = _ => dResolve();
                                        });
                                    }
                                    i++;
                                }   
                            }
                        }
                        db.close();
                        resolve();
                    }
                });
            }
        };
        document.pySessionHandler.setAllObjectsAsync = async function(idb_data, stLayout, resolve) {
            console.log(idb_data, stLayout);
            await document.pySessionHandler.setAllObjects(idb_data, stLayout);
            resolve();
        };
        ''')
        self.__log.debug('setIDBObjects function inserted.')

        self.__log.info('Writing IDB data...')
        self.__driver.execute_async_script('''
        var callback = arguments[arguments.length - 1];
        document.pySessionHandler.setAllObjectsAsync(arguments[0], arguments[1], callback);
        ''', idb.as_dict(), self.__session.get_idb_st_layout() if self.__session.idb_special_treatment else None)
        if self.__session.idb_special_treatment:
            self.__log.info("IDB special treatment required. Running special actions...")
            st_layout = self.__session.get_idb_st_layout()
            st_data = {}
            for st_db, st_os_list in st_layout.items():
                st_data[st_db] = {}
                for st_os in st_os_list:
                    st_data[st_db][st_os] = idb.get_db(st_db).get_object_store(st_os).get_data()
            self.__session.do_idb_st_set_action(self.__driver, st_data)

        self.__log.info("Finished writing data to IDB!")

    def __verify_profile_name_exists(self, profile_name: str) -> bool:
        if self.__custom_driver:
            raise AssertionError('Do not call this method if you are using a custom webdriver.')
        # NOTE: Is this still required?
        if not isinstance(profile_name, str):
            raise TypeError('The provided profile_name is not a string.')

        return True if profile_name in self.__browser_profile_list else False

    def __wait_for_login(self, timeout=120):
        login_success = True
        self.__log.info('Waiting for login... [Timeout: %ss]', timeout)
        # TODO: rewrite this for the general approach
        self.__log.debug(f'Waiting until {self.__session.get_name()} finished loading...')
        try:
            WebDriverWait(self.__driver, 120).until(
                ec.visibility_of_element_located((By.TAG_NAME, 'h1'))
            )
            self.__log.info('Login completed.')
        except TimeoutException:
            login_success = False
            self.__log.error('Login was not completed in time. Aborting...')
        return login_success

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

            self.__log.info(f'Loading {self.__session.get_name()}...')
            self.__driver.get(self.__session.get_url())

            if wait_for_login:
                if not self.__wait_for_login():
                    return
        else:
            self.__log.info('Starting browser... [HEADLESS: %s]', str(options.headless))
            if self.__browser_choice == Browser.CHROME:
                options.add_argument('user-data-dir=%s' % os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Chrome(options=options)
            elif self.__browser_choice == Browser.FIREFOX:
                fire_profile = webdriver.FirefoxProfile(os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Firefox(fire_profile, options=options)

            self.__log.info(f'Loading {self.__session.get_name()}...')
            self.__driver.get(self.__session.get_url())

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

    def __get_profile_session(self, profile_name: Optional[str] = None) -> SessionObject:
        if profile_name is None:
            if self.__custom_driver:
                self.__start_session()
            else:
                self.__start_visible_session()
        else:
            self.__start_invisible_session(profile_name)

        cookies = self.__get_cookies()
        local_storage = self.__get_local_storage()
        indexed_db = self.__get_indexed_db()

        if not self.__custom_driver:
            self.__log.info("Closing browser...")
            self.__driver.quit()
        else:
            self.__log.info("Closing tab...")
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[-1])

        return SessionObject(self.__session.get_name(), self.__session.get_url(), self.__session.get_file_ext(),
                             cookies, local_storage, indexed_db)

    # FIXME: get and set methods do very different things
    def __set_profile_session(self, session_object: SessionObject) -> NoReturn:
        self.__set_cookies(session_object.cookies)
        self.__set_local_storage(session_object.local_storage)
        self.__set_indexed_db(session_object.indexed_db)

        self.__log.info(f'Reloading {self.__session.get_name()}...')
        self.__driver.refresh()

    def __init__(self, session_class: SessionObject,
                 browser: Optional[Union[Browser, str]] = None,
                 driver: Optional[Union[c_wd.WebDriver, f_wd.WebDriver]] = None):
        self.__log = logging.getLogger('SessionHandler')
        self.__log.setLevel(logging.DEBUG)

        self.__platform = platform.system().lower()
        if self.__platform != 'windows' and self.__platform != 'linux':
            raise NotImplementedError('Only Windows and Linux are supported for now.')
        self.__log.debug('Detected platform: %s', self.__platform)

        self.__session = session_class

        if driver:
            self.set_custom_webdriver(driver)
        else:
            if browser:
                self.set_browser(browser)
            else:
                raise ValueError('Parameter browser is empty.\n'
                                 'You need to set a browser or a custom driver during init.')
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
        'dict[str, SessionObject]', 'SessionObject'
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
                return self.__get_profile_session()
            elif use_profile and use_profile in self.__browser_profile_list:
                use_profile_list.append(use_profile)
            elif isinstance(use_profile, list):
                use_profile_list.extend(use_profile)
            else:
                raise ValueError(
                    'Invalid profile provided. Make sure you provided a list of profiles or a profile name.'
                )

        for profile in use_profile_list:
            profile_storage_dict[profile] = self.__get_profile_session(profile)

        return profile_storage_dict

    def create_new_session(self) -> 'SessionObject':
        return self.__get_profile_session()

    def open_session(self) -> SessionObject:
        if not self.__custom_driver:
            self.__start_visible_session(wait_for_login=False)
        else:
            self.__start_session(wait_for_login=False)

        self.__set_profile_session(self.__session)

        return_session = SessionObject(
            self.__session.get_name(),
            self.__session.get_url(),
            self.__session.get_file_ext(),
            self.__get_cookies(),
            self.__get_local_storage(),
            self.__get_indexed_db()
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
        return return_session
