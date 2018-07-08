from distutils.core import setup
import py2exe

# you may have to change paths and copy those files to dist dir
wd_path = 'D:\\Python27\\Lib\\site-packages\\selenium\\webdriver'
required_data_files = ['geckodriver.exe', 'chromedriver.exe', ('selenium/webdriver/firefox',
                        ['{}\\firefox\\webdriver.xpi'.format(wd_path), '{}\\remote\\isDisplayed.js'.format(wd_path),
                         '{}\\firefox\\webdriver_prefs.json'.format(wd_path), '{}\\remote\\getAttribute.js'.format(wd_path)])]

setup(
    console = ['WAWebTransfer.py'],
    data_files = required_data_files,
    options = {
               "py2exe":{
                   "skip_archive": True,
                        }
               }
)
