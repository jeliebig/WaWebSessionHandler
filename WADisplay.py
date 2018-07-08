from selenium import webdriver
import selenium.common.exceptions as webexcept
import os

localStorage = []
count = 1
notready = True

files = os.listdir("saves")
for file in files:
    print ("[%s]    " % str(count)) + file
    count = count + 1
choose = raw_input("Select a number: ")
while notready:
    try:
        choose = int(choose)
        notready = False
        if len(files) < choose:
            choose = raw_input("Select a number: ")
            notready = True
    except:
        notready = True
        choose = raw_input("Select a number: ")
user = files[choose - 1]
notready = True
print "[1]  Firefox"
print "[2]  Chrome"
browser = raw_input("Select a number: ")
while notready:
    try:
        browser = int(browser)
        notready = False
        if 2 < choose:
            choose = raw_input("Select a number: ")
            notready = True
    except:
        notready = True
        browser = raw_input("Select a number: ")
if browser == 1:
    driver = webdriver.Firefox()
if browser == 2:
    driver = webdriver.Chrome()
driver.get("https://web.whatsapp.com")
with open("saves\\" + user, "r") as take:
    localStorageFile = take.readlines()
for var in localStorageFile:
    var.strip("\n")
    localStorage.append(var.replace("\n", ""))
for split in localStorage:
    up = str(split)
    eyy = up.split(": ")
    driver.execute_script(("window.localStorage.setItem('%s', '%s')" % (eyy[0], eyy[1])))
driver.refresh()
raw_input("Press Enter to close WhatsApp Web ")
try:
    driver.quit()
except webexcept.WebDriverException:
    print "The webdriver process is still running. Pls stop it manually."
