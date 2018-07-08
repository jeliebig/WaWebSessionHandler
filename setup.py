from distutils.core import setup
import py2exe

# make sure you have 32bit py2exe installed
# you may have to change    paths and copy those files to dist dir
wd_path = 'D:\\Python27\\Lib\\site-packages\\selenium\\webdriver'
required_data_files = [('selenium/webdriver/firefox', 
                        ['{}\\firefox\\webdriver.xpi'.format(wd_path), '{}\\remote\\isDisplayed.js'.format(wd_path),
                         '{}\\firefox\\webdriver_prefs.json'.format(wd_path), '{}\\remote\\getAttribute.js'.format(wd_path)])]

setup(
    console = ['WAWebTransfer.pyw'],
    data_files = required_data_files,
    options = {
               "py2exe":{
                   "skip_archive": True,
                   "bundle_files": 1,
                   "compressed": True,
                        }
               }
)
