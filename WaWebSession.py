import os
import platform

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as fireOptions


# Stack Overflow Code but I don't have the source anymore :/
def get(driver, key=None):
    if key:
        return driver.execute_script('return window.localStorage.getItem("{}")'.format(key))
    else:
        return driver.execute_script('''
        var items = {}, ls = window.localStorage;
        for (var i = 0, k; i < ls.length; i++)
          items[k = ls.key(i)] = ls.getItem(k);
        return items;
        ''')


class WaWebSession:
    def __init__(self, browser=None):
        try:
            self.platform = platform.system().lower()
            if self.platform == 'windows':
                self.cd = '\\'
            else:
                self.cd = '/'
            self.driver = None
            self.path = os.path.dirname(os.path.realpath(__file__))
            self.pStorage = {}
            self.Storage = {}
            if browser:
                if browser.lower() == 'chrome':
                    self.choice = 1
                elif browser.lower() == 'firefox':
                    self.choice = 2
                else:
                    print('Browser not supported.'
                          'Please use WaWebSession(browser="chrome")'
                          '           WaWebSession(browser="firefox")'
                          'or         WaWebSession()')
                    raise SyntaxError
            else:
                print('1) Chrome\n'
                      '2) Firefox\n')
                self.choice = int(input('Select a number from the list: '))
            if self.choice == 1:
                self.Options = webdriver.ChromeOptions()
                self.Options.headless = True
                if self.platform == 'windows':
                    self.dir = os.environ['USERPROFILE'] + '\\Appdata\\Local\\Google\\Chrome\\User Data'
                elif self.platform == 'linux':
                    self.dir = os.environ['HOME'] + '/.config/google-chrome'
                else:
                    print('Only Windows and Linux are working by now.')
                    raise OSError
                self.profiles = []
                self.profiles.append('')
                for profileDir in os.listdir(self.dir):
                    if 'Profile' in profileDir:
                        if profileDir != 'System Profile':
                            self.profiles.append(profileDir)
            else:
                self.Options = fireOptions()
                self.Options.headless = True
                if self.platform == 'windows':
                    self.dir = os.environ['APPDATA'] + '\\Mozilla\\Firefox\\Profiles'
                    self.profiles = os.listdir(self.dir)
                elif self.platform == 'linux':
                    self.dir = os.environ['HOME'] + '/.mozilla/firefox'
                    # TODO: consider reading out the profiles.ini
                    self.profiles = []
                    for profileDir in os.listdir(self.dir):
                        if '.default' in profileDir:
                            if os.path.isdir(self.dir + '/' + profileDir):
                                self.profiles.append(profileDir)
                else:
                    print('Only Windows and Linux are working by now.')
                    raise OSError
        except Exception as e:
            print('Something went wrong: ', e)
            exit(1)

    def get_active(self, profile=None):
        print('Make sure your browser is closed.')
        self.pStorage = {}
        self.Storage = {}
        if profile:
            if self.choice == 1:
                chrome_profile = self.Options
                chrome_profile.add_argument('user-data-dir=%s' % self.dir + self.cd + profile)
                if self.platform == 'linux':
                    self.driver = webdriver.Chrome((self.path + '/chromedriver'), options=chrome_profile)
                else:
                    self.driver = webdriver.Chrome(options=chrome_profile)
            else:
                fire_profile = webdriver.FirefoxProfile(self.dir + self.cd + profile)
                if self.platform == "windows":
                    self.driver = webdriver.Firefox(fire_profile, options=self.Options)
                elif self.platform == "linux":
                    self.driver = webdriver.Firefox(fire_profile, executable_path=(self.path + '/geckodriver'),
                                                    options=self.Options)
            self.driver.get('https://web.whatsapp.com/')
            for key, value in get(self.driver).items():
                try:
                    self.Storage[key] = value
                except UnicodeEncodeError:
                    pass
            self.driver.quit()
            return self.Storage
        else:
            for file in self.profiles:
                if self.choice == 1:
                    chrome_profile = self.Options
                    chrome_profile.add_argument('user-data-dir=%s' % self.dir + self.cd + file)
                    if self.platform == 'linux':
                        self.driver = webdriver.Chrome((self.path + '/chromedriver'), options=chrome_profile)
                    else:
                        self.driver = webdriver.Chrome(options=chrome_profile)
                else:
                    fire_profile = webdriver.FirefoxProfile(self.dir + self.cd + file)
                    if self.platform == "windows":
                        self.driver = webdriver.Firefox(fire_profile, options=self.Options)
                    elif self.platform == "linux":
                        self.driver = webdriver.Firefox(fire_profile, executable_path=(self.path + '/geckodriver'),
                                                        options=self.Options)
                self.Storage = {}
                self.driver.get('https://web.whatsapp.com/')
                for key, value in get(self.driver).items():
                    try:
                        self.Storage[key] = value
                    except UnicodeEncodeError:
                        pass
                self.pStorage[file] = self.Storage
                self.driver.quit()
            return self.pStorage

    def create_new(self):
        options = self.Options
        options.headless = False
        if self.choice == 1:
            if self.platform == 'linux':
                self.driver = webdriver.Chrome((self.path + '/chromedriver'), options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        else:
            if self.platform == 'linux':
                self.driver = webdriver.Firefox(executable_path=(self.path + '/geckodriver'),
                                                options=options)
            else:
                self.driver = webdriver.Firefox(options=options)
        self.driver.get('https://web.whatsapp.com/')
        input('Please log in and press Enter...')
        for key, value in get(self.driver).items():
            try:
                self.Storage[key] = value
            except UnicodeEncodeError:
                pass
        self.driver.quit()
        return self.Storage

    def view(self, s_dict=None, file=None):  # TODO: improve view method | maybe if dict could help
        if not s_dict and not file:
            print('No arguments.\n'
                  'Please use view(dict=localStorage_dict)\n'
                  'or         view(file="path")\n')
            raise SyntaxError
        if "\\" in file:
            file = file.replace("\\", "/")
        options = self.Options
        options.headless = False
        if self.choice == 1:
            if self.platform == 'linux':
                self.driver = webdriver.Chrome((self.path + '/chromedriver'), options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        else:
            if self.platform == 'linux':
                self.driver = webdriver.Firefox(executable_path=(self.path + '/geckodriver'),
                                                options=options)
            else:
                self.driver = webdriver.Firefox(options=options)
        if file:
            with open(file, 'r') as stor:
                lsfile = stor.readlines()
            lines = []
            for line in lsfile:
                line = line.replace('\n', '')
                if line != '':
                    lines.append(line)
            self.driver.get('https://web.whatsapp.com/')
            for line in lines:
                line = str(line)
                stor = line.split(' : ')
                self.driver.execute_script(("window.localStorage.setItem('%s', '%s')" % (stor[0], stor[1])))
            self.driver.refresh()
            input('Press Enter to close WhatsApp Web...')
            self.driver.quit()
        elif str(type(s_dict)) == '<class "dict">':
            for item in s_dict:
                if str(type(s_dict[item])) != '<class "str">':
                    print('Format of dict should be > key:value')
                    raise SyntaxError
                else:
                    if self.choice == 1:
                        if self.platform == 'linux':
                            self.driver = webdriver.Chrome((self.path + '/chromedriver'), chrome_options=options)
                        else:
                            self.driver = webdriver.Chrome(chrome_options=options)
                    else:
                        if self.platform == 'linux':
                            self.driver = webdriver.Firefox(executable_path=(self.path + '/geckodriver'),
                                                            options=options)
                        else:
                            self.driver = webdriver.Firefox(options=options)
                    self.driver.get('https://web.whatsapp.com/')
                    for key in s_dict:
                        self.driver.execute_script(("window.localStorage.setItem('%s', '%s')" % (key, s_dict[key])))
                    self.driver.refresh()
                    input('Press Enter to close WhatsApp Web...')
                    self.driver.quit()
        else:
            print('Format of dict should be > key:value')
            raise SyntaxError

    def save2file(self, session, path, name=None):
        if name:
            try:
                name = str(name)
            except Exception:
                print('Name requires a string')
                raise SyntaxError
        try:  # Is there a better way to do that?
            if os.path.isdir(path):
                pass
        except Exception as e:
            print('Folder does not exist.\n', e)
            raise os.error
        if str(type(session)) == "<class 'dict'>":
            for item in session:
                if str(type(session[item])) == "<class 'str'>":
                    single = True
                    if name:
                        if os.path.isfile(path + self.cd + name + '.lwa'):
                            print('File already exists.')
                            raise os.error
                        with open(path + self.cd + name + '.lwa', 'a') as file:
                            try:
                                file.writelines(item + ' : ' + session[item])
                            except UnicodeEncodeError:
                                pass

                elif str(type(session[item])) == "<class 'dict'>":
                    single = False
                    if name:
                        if item == "":
                            if os.path.isfile(path + self.cd + name + '.lwa'):
                                print('File already exists.')
                                raise os.error
                        else:
                            if os.path.isfile(path + self.cd + name + '-' + item + '.lwa'):
                                print('File already exists.')
                                raise os.error
                    else:
                        if item == "":
                            if os.path.isfile(path + self.cd + 'SessionFile.lwa'):
                                print('File already exists.')
                                raise os.error
                        else:
                            if os.path.isfile(path + self.cd + 'SessionFile-' + item + '.lwa'):
                                print('File already exists.')
                                raise os.error

                    for key in session[item]:
                        if name:
                            if item == "":
                                with open(path + self.cd + name + '.lwa', 'a') as file:
                                    try:
                                        file.write(key + ' : ' + session[item][key] + '\n')
                                    except UnicodeEncodeError:
                                        pass
                            else:
                                with open(path + self.cd + name + '-' + item + '.lwa', 'a') as file:
                                    try:
                                        file.write(key + ' : ' + session[item][key] + '\n')
                                    except UnicodeEncodeError:
                                        pass
                        else:
                            if item == "":
                                with open(path + self.cd + 'SessionFile.lwa', 'a') as file:
                                    try:
                                        file.write(key + ' : ' + session[item][key] + '\n')
                                    except UnicodeEncodeError:
                                        pass
                            else:
                                with open(path + self.cd + 'SessionFile-' + item + '.lwa', 'a') as file:
                                    try:
                                        file.write(key + ' : ' + session[item][key] + '\n')
                                    except UnicodeEncodeError:
                                        pass
                    if name:
                        if item == "":
                            print('File saved to: ' + path + self.cd + name + '.lwa')
                        else:
                            print('File saved to: ' + path + self.cd + 'SessionFile-' + item + '.lwa')
                    else:
                        if item == "":
                            print('File saved to: ' + path + self.cd + 'SessionFile.lwa')
                        else:
                            print('File saved to: ' + path + self.cd + 'SessionFile-' + item + '.lwa')
                else:
                    print("Please check your session dict. It should provide a string or dict\n"
                          "Read: https://github.com/jeliebig/WAWebSessionHandler#session-dict-design\n")
                    raise SyntaxError
            if single:
                if name:
                    print('File saved to: ' + path + self.cd + name + '.lwa')
                else:
                    print('File saved to: ' + path + self.cd + 'SessionFile.lwa')
        else:
            print('Input should be a dict with profiles and localStorage or a dict with key and value')
            # TODO: improve Error msg
            raise SyntaxError


if __name__ == '__main__':
    web = WaWebSession()
    print('1) Save session to file\n'
          '2) View session from a file\n')
    choice = int(input('Select a number from the list: '))
    if choice == 2:
        web.view(file=input('Enter file path: '))
    else:
        if not os.path.isdir('saves'):
            os.mkdir('saves')
        web.save2file(web.get_active(), 'saves', name=input("Enter a name for the file: "))
