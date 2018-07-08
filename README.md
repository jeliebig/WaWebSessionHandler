# WAWebSessionTransfer
Save a Whatsapp Web Session to a file and run it everywhere! 

# Requirements:
If you want to run the .py files you will need:
- Chrome or Firefox
- Selenium (pip install selenium)
- optional: py2exe 32bit

# How to use:
Run WAWebTransfer.py and it will scan Firefox and Chrome for a whatsapp web session that will be saved at saves/"username"@"hostname".lwa
Now you can run WADisplay.py to open Chrome or Firefox with a session that you stored in the saves directory

# Known Issues:

- If you use Google Chrome with different profiles WAWebTransfer.py will only take the session from the default profile.
- If you close the browser window of WADisplay.py the webdriver will still be running. (make sure to close it through the console window)
