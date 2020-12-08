import json
import logging
import os
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException


class WaWebSession:
    URL = 'https://web.whatsapp.com/'
    CHROME = 1
    FIREFOX = 2

    def __init_browser(self):
        if self.browser_choice == self.CHROME:
            self.browser_options = webdriver.ChromeOptions()

            if self.platform == 'windows':
                self.browser_user_dir = os.path.join(os.environ['USERPROFILE'],
                                                     'Appdata', 'Local', 'Google', 'Chrome', 'User Data')
            elif self.platform == 'linux':
                self.browser_user_dir = os.path.join(os.environ['HOME'], '.config', 'google-chrome')

        elif self.browser_choice == self.FIREFOX:
            self.browser_options = webdriver.FirefoxOptions()

            if self.platform == 'windows':
                self.browser_user_dir = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
                self.browser_profile_list = os.listdir(self.browser_user_dir)
            elif self.platform == 'linux':
                self.browser_user_dir = os.path.join(os.environ['HOME'], '.mozilla', 'firefox')

        self.browser_options.headless = True
        self.__refresh_profile_list()

    def __refresh_profile_list(self):
        if self.browser_choice == self.CHROME:
            self.browser_profile_list = ['']
            for profile_dir in os.listdir(self.browser_user_dir):
                if 'profile' in profile_dir.lower():
                    if profile_dir != 'System Profile':
                        self.browser_profile_list.append(profile_dir)
        elif self.browser_choice == self.FIREFOX:
            # TODO: consider reading out the profiles.ini
            self.browser_profile_list = []
            for profile_dir in os.listdir(self.browser_user_dir):
                if not profile_dir.endswith('.default'):
                    if os.path.isdir(os.path.join(self.browser_user_dir, profile_dir)):
                        self.browser_profile_list.append(profile_dir)

    def __get_indexed_db(self):
        self.driver.execute_script('window.waScript = {};'
                                   'window.waScript.waSession = undefined;'
                                   'function getAllObjects() {'
                                   'window.waScript.dbName = "wawc";'
                                   'window.waScript.osName = "user";'
                                   'window.waScript.db = undefined;'
                                   'window.waScript.transaction = undefined;'
                                   'window.waScript.objectStore = undefined;'
                                   'window.waScript.getAllRequest = undefined;'
                                   'window.waScript.request = indexedDB.open(window.waScript.dbName);'
                                   'window.waScript.request.onsuccess = function(event) {'
                                   'window.waScript.db = event.target.result;'
                                   'window.waScript.transaction = window.waScript.db.transaction('
                                   'window.waScript.osName);'
                                   'window.waScript.objectStore = window.waScript.transaction.objectStore('
                                   'window.waScript.osName);'
                                   'window.waScript.getAllRequest = window.waScript.objectStore.getAll();'
                                   'window.waScript.getAllRequest.onsuccess = function(getAllEvent) {'
                                   'window.waScript.waSession = getAllEvent.target.result;'
                                   '};'
                                   '};'
                                   '}'
                                   'getAllObjects();')
        while not self.driver.execute_script('return window.waScript.waSession != undefined;'):
            time.sleep(1)
        wa_session_list = self.driver.execute_script('return window.waScript.waSession;')
        self.log.debug("Got IDB data: %s", wa_session_list)
        return wa_session_list

    def __get_profile_storage(self, profile_name=None):
        self.__refresh_profile_list()

        if profile_name is not None and profile_name not in self.browser_profile_list:
            raise ValueError

        if profile_name is None:
            self.__start_visible_session()
        else:
            self.__start_invisible_session(profile_name)

        indexed_db = self.__get_indexed_db()

        self.driver.quit()
        return indexed_db

    def __start_session(self, options, profile_name=None, wait_for_login=True):
        self.log.debug("Starting browser...")
        if profile_name is None:
            if self.browser_choice == self.CHROME:
                self.driver = webdriver.Chrome(options=options)
            elif self.browser_choice == self.FIREFOX:
                self.driver = webdriver.Firefox(options=options)

            self.log.debug("Loading WhatsApp Web...")
            self.driver.get(self.URL)

            if wait_for_login:
                self.log.debug("Waiting for login...")
                verified_wa_profile_list = False
                while not verified_wa_profile_list:
                    time.sleep(1)
                    verified_wa_profile_list = False
                    for object_store_obj in self.__get_indexed_db():
                        if "WASecretBundle" in object_store_obj["key"]:
                            verified_wa_profile_list = True
                            break
                self.log.debug("Login completed.")
        else:
            if self.browser_choice == self.CHROME:
                options.add_argument('user-data-dir=%s' % os.path.join(self.browser_user_dir, profile_name))
                self.driver = webdriver.Chrome(options=options)
            elif self.browser_choice == self.FIREFOX:
                fire_profile = webdriver.FirefoxProfile(os.path.join(self.browser_user_dir, profile_name))
                self.driver = webdriver.Firefox(fire_profile, options=options)

            self.log.debug("Loading WhatsApp Web...")
            self.driver.get(self.URL)

    def __start_visible_session(self, profile_name=None, wait_for_login=True):
        options = self.browser_options
        options.headless = False
        self.__refresh_profile_list()

        if profile_name is not None and profile_name not in self.browser_profile_list:
            raise ValueError

        self.__start_session(options, profile_name, wait_for_login)

    def __start_invisible_session(self, profile_name=None):
        self.__refresh_profile_list()
        if profile_name is not None and profile_name not in self.browser_profile_list:
            raise ValueError

        self.__start_session(self.browser_options, profile_name)

    def __init__(self, browser=None):
        self.log = logging.getLogger('WaWebSession')
        self.log_format = logging.Formatter('%(asctime)s [%(levelname)s] (%(funcName)s): %(message)s')
        self.log_level = logging.DEBUG
        self.log.setLevel(self.log_level)

        log_stream = logging.StreamHandler()
        log_stream.setLevel(self.log_level)
        log_stream.setFormatter(self.log_format)
        self.log.addHandler(log_stream)

        self.platform = platform.system().lower()
        if self.platform != 'windows' and self.platform != 'linux':
            self.log.error('Only Windows and Linux are supported for now.')
            raise OSError

        self.path = os.path.dirname(os.path.realpath(__file__))
        self.browser_choice = 0
        self.browser_options = None
        self.browser_user_dir = None
        self.driver = None

        if browser:
            if browser != self.CHROME and browser != self.FIREFOX:
                self.log.error('Browser not supported.'
                               'Please use WaWebSession(browser=WaWebSession.CHROME)'
                               '           WaWebSession(browser=WaWebSession.FIREFOX)'
                               'or         WaWebSession()')
                raise ValueError
            else:
                self.browser_choice = browser

        else:
            while self.browser_choice != self.CHROME and self.browser_choice != self.FIREFOX:
                print('1) Chrome\n'
                      '2) Firefox\n')
                self.browser_choice = int(input('Select a browser by choosing a number from the list: '))
        self.__init_browser()

    def get_active_session(self, use_profile=None):
        self.log.info('Make sure your browser profile is not in use.')
        profile_storage_dict = {}
        use_profile_list = []
        self.__refresh_profile_list()

        if use_profile and use_profile not in self.browser_profile_list:
            self.log.error("Profile does not exist: %s", use_profile)
            raise ValueError
        elif use_profile is None:
            return self.__get_profile_storage()
        elif use_profile and use_profile in self.browser_profile_list:
            use_profile_list.append(use_profile)
        else:
            use_profile_list.extend(self.browser_profile_list)

        for profile in use_profile_list:
            profile_storage_dict[profile] = self.__get_profile_storage(profile)

        return profile_storage_dict

    def create_new_session(self):
        return self.__get_profile_storage()

    def access_by_dict(self, wa_profile_list):
        verified_wa_profile_list = False
        for object_store_obj in wa_profile_list:
            if "WASecretBundle" in object_store_obj["key"]:
                verified_wa_profile_list = True
                break

        if not verified_wa_profile_list:
            self.log.error("This is not a valid profile list. Make sure you only pass one session to this method.")
            raise ValueError

        self.__start_visible_session(wait_for_login=False)
        self.log.debug("Inserting setObject function...")
        self.driver.execute_script('window.waScript = {};'
                                   'window.waScript.insertDone = 0;'
                                   'window.waScript.jsonObj = undefined;'
                                   'window.waScript.setAllObjects = function (_jsonObj) {'
                                   'window.waScript.jsonObj = _jsonObj;'
                                   'window.waScript.dbName = "wawc";'
                                   'window.waScript.osName = "user";'
                                   'window.waScript.db;'
                                   'window.waScript.transaction;'
                                   'window.waScript.objectStore;'
                                   'window.waScript.clearRequest;'
                                   'window.waScript.addRequest;'
                                   'window.waScript.request = indexedDB.open(window.waScript.dbName);'
                                   'window.waScript.request.onsuccess = function(event) {'
                                   'window.waScript.db = event.target.result;'
                                   'window.waScript.transaction = window.waScript.db.transaction('
                                   'window.waScript.osName, "readwrite");'
                                   'window.waScript.objectStore = window.waScript.transaction.objectStore('
                                   'window.waScript.osName);'
                                   'window.waScript.clearRequest = window.waScript.objectStore.clear();'
                                   'window.waScript.clearRequest.onsuccess = function(clearEvent) {'
                                   'for (var i=0; i<window.waScript.jsonObj.length; i++) {'
                                   'window.waScript.addRequest = window.waScript.objectStore.add('
                                   'window.waScript.jsonObj[i]);'
                                   'window.waScript.addRequest.onsuccess = function(addEvent) {'
                                   'window.waScript.insertDone++;'
                                   '};'
                                   '}'
                                   '};'
                                   '};'
                                   '}')
        self.log.debug("Insert done.")
        self.log.debug("Writing IDB data: %s", wa_profile_list)
        self.driver.execute_script('window.waScript.setAllObjects(arguments[0]);', wa_profile_list)

        self.log.debug("Waiting...")
        while not self.driver.execute_script(
                'return (window.waScript.insertDone == window.waScript.jsonObj.length);'):
            time.sleep(1)

        self.driver.refresh()

        while True:
            try:
                _ = self.driver.window_handles
            except WebDriverException:
                break

    def access_by_file(self, profile_file):
        profile_file = os.path.normpath(profile_file)

        if os.path.isfile(profile_file):
            with open(profile_file, "r") as file:
                wa_profile_list = json.load(file)

            verified_wa_profile_list = False
            for object_store_obj in wa_profile_list:
                if "WASecretBundle" in object_store_obj["key"]:
                    verified_wa_profile_list = True
                    break
            if verified_wa_profile_list:
                self.access_by_dict(wa_profile_list)
            else:
                self.log.error("This is not a valid profile list. Make sure you only pass one session to this method.")
                raise ValueError
        else:
            raise FileNotFoundError

    def save_profile(self, wa_profile_list, file_path):
        file_path = os.path.normpath(file_path)

        verified_wa_profile_list = False
        for object_store_obj in wa_profile_list:
            if "WASecretBundle" in object_store_obj["key"]:
                verified_wa_profile_list = True
                break
        if verified_wa_profile_list:
            with open(file_path, "w") as file:
                json.dump(wa_profile_list, file, indent=4)
        else:
            for profile_name in wa_profile_list.keys():
                profile_storage = wa_profile_list[profile_name]
                verified_wa_profile_list = False
                for object_store_obj in profile_storage:
                    if "WASecretBundle" in object_store_obj["key"]:
                        verified_wa_profile_list = True
                        break
                if verified_wa_profile_list:
                    single_profile_name = os.path.basename(file_path) + "-" + profile_name
                    self.save_profile(profile_storage, os.path.join(os.path.dirname(file_path), single_profile_name))


if __name__ == '__main__':
    web = WaWebSession()
    choice = 0
    while choice != 1 and choice != 2:
        print('1) Save session to file\n'
              '2) View session from a file\n')
        choice = int(input('Select an option from the list: '))

    if choice == 1:
        web.save_profile(web.get_active_session(), input('Enter a file path for the generated file: '))
        print("File saved.")
    elif choice == 2:
        web.access_by_file(input('Enter a file path: '))
