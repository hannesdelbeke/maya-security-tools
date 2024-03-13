# Maya security tools - module
rehost of Maya security tools 1.0.3 - a.k.a. MayaScanner https://apps.autodesk.com/MAYA/en/Detail/Index?id=8637238041954239715&os=Win64&appLang=en

1. Install the maya security tools.
2. After installation, load the plugin in Maya.
   - From the menu `windows / settings-preferences / plugin manager`, open the plugin manager.
   - Search for `scanner` and check the `load` and `auto load` checkboxes for both `MayaScanner` and `MayaScannerCB`

--- 

# Readme

## Maya Security Tools
Maya Security Tools installs two Maya plug-ins: `MayaScanner.py` and `MayaScannerCB.py`. These plug-ins 
are used to scan Maya scene files and startup scripts for malicious scripts. If malicious scripts are 
detected, an option to clean the files is provided.

⚠️ MayaScanner.py and MayaScannerCB.py are not loaded by default. You will need to load them from the 
Plug-in Manager.

### Running from Within Maya
When MayaScanner is loaded, two new items, Scan File and Scan Current Scene, are added to the File 
menu. Scan File lets you select a Maya scene file for scanning, while Scan Current Scene will scan the 
currently loaded scene file.

When MayaScannerCB is loaded, scene files are automatically scanned when they are loaded into Maya.

⚠️ Note: Scanning is not done recursively. If a scene file contains references, each referenced file needs to 
be scanned individually. This means that each file needs to be scanned using Scan File, or loaded into 
Maya and scanned using Scan Current Scene.

If the scene files are clean, the message “Scan completed: no issues found” will be printed in the script 
editor.

If a malicious script is detected in the file, a warning will be generated, and a pop-up window will 
prompt you to either clean the file or quit.

If you opt to clean the file, you will further be prompted to save the file and quit, or quit without saving.
If a file is being imported into a new unsaved scene without a name, there will be no option to save. 
Maya will quit in this instance.

Note: Maya must quit and restart to return to a clean session.

### Running in Interactive Mode 
To scan and clean a scene file in interactive mode on Windows, use
```
maya -file "<scene_file>" -command "evalDeferred (\"loadPlugin MayaScanner; MayaScan;\")"
```
To scan and clean a scene file in interactive mode on Linux or macOS, use
```
maya -file '<scene_file>' -command 'evalDeferred("loadPlugin MayaScanner;MayaScan;")'
```

### Running in Batch Mode
To scan and clean a scene file in batch mode on Windows, use
```
maya -batch -file "<scene_file>" -command "evalDeferred (\"loadPlugin MayaScanner; MayaScan;\")"
```
To scan and clean a scene file in batch mode on Linux or macOS, use
```
maya -batch -file '<scene_file>' -command 'evalDeferred("loadPlugin MayaScanner;MayaScan;")'
```
Files are automatically cleaned and saved when running in batch mode.

Note: UI configurations will not be saved on exit when Maya is operating in batch mode.

### Logging
Maya Security Tools writes logs to MayaScannerLog.txt in %TMPDIR% on Windows and $TMPDIR on 
Linux and macOS.

---

## Maya Security Tools Admin Scripts Guide
Maya Security Tools includes three administrative clean up scripts: cleanScriptNode, scanAndCleanScriptNode, and cleanUserSetup.

These are located under the Maya Security Tools installation directory:
- Linux: `/usr/autodesk/ApplicationPlugins/<app name>` or `~/Autodesk/ApplicationPlugins/<app name>`
- macOS: `/Users/Shared/Autodesk/ApplicationAddins/<app name>`
- Windows: `%programdata%\Autodesk\ApplicationPlugins\<app name>`
  Note: You will need to install Cygwin or another bash emulator to run these scripts on Windows.
  
### cleanUserSetup
cleanUserSetup takes as a user setup file as an argument. It scans the setup file for malicious elements, 
removes them, and saves the modified file.

### cleanScriptNode
cleanScriptNode takes a script node as an argument. It scans the node for malicious elements. If 
malicious elements are found, they are removed, the file is saved, and a backup of the original is made.

### scanAndCleanScriptNode
scanAndCleanScriptNode takes a directory as an argument. It goes through a directory recursively, 
scanning and cleaning all the script nodes in the directory tree. If malicious elements are found in a 
script node, the script node will be cleaned and saved, and a backup of the original is made

---
