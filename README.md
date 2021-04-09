# WaWebSessionHandler

Save WhatsApp Web Sessions to files and run them everywhere! 

## Requirements:

If you want to run the .py file you will need:
- Chrome or Firefox
- Selenium (pip install selenium)
- Chromedriver and/or Geckodriver
    - copy them in the same folder as the scrip, or put them in PATH
    - Note: Make sure they can be executed by the script

## How to use:

You could simply run "WaWebSession.py" and use it as a script, or import the "SessionHandler"-Class in your own script and work with it that way.

## Class(es) and Methods:

- wa_sh = WaWebSession.SessionHandler() -> creates a new instance of the SessionHandler
    - you can also specify two optional parameters:
        - browser -> can be Browser.CHROME or Browser.FIREFOX
        - log_level -> can be a level of the logging module, or a string of the wanted level
- wa_sh.set_browser(browser) -> change the browser used by this class
- wa_sh.set_log_level(log_level) -> change the log_level of this module
- wa_sh.create_new_session() -> extracts a new WaWebProfile from a temporary browser session (login prompt)
    - returns a list with all stored IDB user objects (also referred to as: WaWebSession object, profile_obj,
      session_obj)
- wa_sh.get_active_session() -> gets all active sessions from the browser
    - you can also specify a profile by using the "profile" parameter passing a single name, or a list of profile names
      to it
    - returns a dict that looks like this: {profile_name: profile_obj}
- wa_sh.access_by_obj(profile_obj) -> starts the provided session in a browser window
- wa_sh.access_by_file(filepath) -> starts the provided session in a browser window
- wa_sh.save_profile(profile_obj, filepath) -> creates a session file from a profile_obj
    - you can also save multiple profiles by providing a dict like the one returned by get_active_session()
    - filepath can be a relative or absolute path
 
## IDB user object file:

- session objects are stored in a list
- the items in the list are dicts looking like this: {"key": entry_key, "value": entry_value}
- the list is extracted from the "user" objectStore of the WhatsApp Web page
