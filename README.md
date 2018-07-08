# WAWebSessionTransfer
Save Whatsapp Web Sessions to a file and run it everywhere! 

# Requirements:
If you want to run the .py files you will need:
- Chrome or Firefox
- Selenium (pip install selenium)
- Chromedriver and Geckodriver (copy them in the same folder as the scripts)
- optional: py2exe 32bit (could also work with 64bit)

# How to use:
Run WAWebTransfer.py and it will scan Firefox and Chrome for a whatsapp web session that will be saved at saves/"username"@"hostname".lwa.
Now you can run WADisplay.py to open Chrome or Firefox with a session that you stored in the saves directory

# Build Windows exe:
- Check if the paths in the setup.py are correct for you
- Open cmd in the folder with the scripts and run: "setup.py py2exe"
you may have to change the command if it uses the wrong python interpreter
- create a saves folder in the dist directory
- to make it protable: copy the dist folder to an usb-drive and create a link to the WAWebTransfer.exe from the dist folder to the root folder (if you want you can change the settings of the console window in the properties of the link file)

# Known Issues:

- If you use Google Chrome with different profiles WAWebTransfer.py will only take the session from the default profile.
- If you close the browser window of WADisplay.py the webdriver will still be running. (make sure to close it through the console window)
- py2exe is not able to build a single executable
