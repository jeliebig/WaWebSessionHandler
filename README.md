# WAWebSessionHandler
Save Whatsapp Web Sessions to files and run them everywhere! 

# Requirements:
If you want to run the .py file you will need:
- Chrome or Firefox
- Selenium (pip install selenium)
- Chromedriver and Geckodriver (copy them in the same folder as the scripts)

# How to use:
You could simply run "WaWebSession.py" and use it as a script, or you could import the "WaWebSession"-Class in your script and work with it.

# Syntax:
-  WaWebSession() -> creates a new instance of WaWebSession()
    - you could choose a between "chrome" and "firefox" with WaWebSession(browser=)
- WaWebSession().create_new() -> gets a session from a new browser session (login prompt)
    - returns a dict
- WaWebSession().get_active() -> gets all the active sessions from a browser
    - you could select a specific profile with WaWebSession.get_active(profile="")
    - returns a dict which contains all the users with session dicts
- WaWebSession().view() -> starts a given session in a browser window
    - you could view a session from a dict with WaWebSession().view(dict=)
    - or start a session from a file with WaWebSession().view(file="")
- WaWebSession().save2file(dict, path) -> creates a session file from a dict
    - the path has to be a string
    - you could also choose a specific name for your files with WaWebSession().save2file(dict, path, name) -> name has to be a string
    - you can also save mutiple profiles, if they are stored in a dict
 
# Session dict design:
- single profile:
    - key -> value
    - dict[key] = value
- multiple profiles:
    - profile -> key -> value
    - dict[profile][key] = value


# Unsupported for now:
Build Windows binary yourself:
- Check if the paths of setup.py are correct for you
- Open cmd in the folder with the scripts and run: "setup.py py2exe" (you may have to change the command if it uses the wrong python interpreter)
- create a saves folder in the dist directory
- to make it portable: copy the dist folder to an usb-drive and create a link to the WAWebTransfer.exe from the dist folder to the root folder (if you want you can change the settings of the console window in the properties of the link file)

Known Issues:
- py2exe is not able to build a single executable
