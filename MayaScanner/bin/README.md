
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
