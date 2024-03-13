########################################################################
# DESCRIPTION:
#
# Produces the command "MayaScan". 
#
# To use, make sure that MayaScanner.py is in your MAYA_PLUG_IN_PATH,
# then do the following:
#
#    import maya
#    maya.cmds.loadPlugin("MayaScanner.py")
#    maya.cmds.MayaScan()
#
########################################################################


import sys
import os

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

from MayaScannerCleaner import clean_malware, MayaScannerLogFile, rollOverLogFile, reportIssue, userConfirmFix
from MayaScannerUtils import FnPlugin, MsgFormat

###########
## 
## beginning of scripted plugin for Scanning scene
##
###########

kScanTypeFlag = "-st"
kScanTypeLongFlag = "-scanType"
kCurrent = 0
kFile = 1
kDirectory = 2

# end of the scan output summary
def endScanSummary(issuesFound, issuesFixed, malType):

    # exit code
    retStatus = 0

    # only need to resave if something has been found
    if issuesFound:

        kSaveAndQuit = 'Save and Quit'
        kQuitWithoutSave = 'Quit without Saving'
        retStatus = 19       # we know issues have been found

        # initial warning on command line
        cmds.warning("Autodesk.MayaScanner : Scan completed: see \'%s\' for issues found" % MayaScannerLogFile())

        typeExtension = 'py'
        if malType == 1:
            typeExtension = 'mel'

        # check to see if we have current scene name to save
        if cmds.file(q=True, sn=True) == "":
            saveRequest = cmds.confirmDialog( 
                title='Autodesk.MayaScanner', 
                message=MsgFormat('Found corrupted scene, No scene name, cannot save.<br>' \
                                  'We recommend that you:<ol>' \
                                  '<li><b>Quit</b> Maya.</li>' \
                                  '<li>Load scene separately or fix offline.</li></ol><br>'),
                messageAlign='center',
                button=[kQuitWithoutSave], 
                defaultButton=kQuitWithoutSave, 
                cancelButton=kQuitWithoutSave, 
                dismissString=kQuitWithoutSave 
            )
        else: 
            # we have scene file name to save, continue
            if issuesFixed < issuesFound:
                saveRequest = cmds.confirmDialog( 
                    title='Autodesk.MayaScanner', 
                    message=MsgFormat('Found corrupted scene, not fully fixed.<br>' \
                                      'We recommend that you:<ol>' \
                                      '<li><b>Quit</b> Maya.<br>' \
                                      '<li>Check userSetup.%s and scene file scriptNodes.</li>' \
                                      '<li>Start new Maya session.</li></ol><br>' % typeExtension),
                    button=[kSaveAndQuit, kQuitWithoutSave], 
                    defaultButton=kQuitWithoutSave, 
                    cancelButton=kQuitWithoutSave, 
                    dismissString=kQuitWithoutSave 
                )
            else:
                saveRequest = cmds.confirmDialog( 
                    title='Autodesk.MayaScanner',
                    message=MsgFormat('Found corrupted scene, attempted to fix.<br>' \
                                      'We recommend that you:<ol>' \
                                      '<li><b>Save</b> current scene.<br>' \
                                      '<li>Quit Maya.</li>' \
                                      '<li>Check userSetup.%s and scene file scriptNodes.</li>' \
                                      '<li>Start new Maya session.</li></ol><br>' % typeExtension),
                    button=[kSaveAndQuit, kQuitWithoutSave], 
                    defaultButton=kSaveAndQuit, 
                    cancelButton=kQuitWithoutSave, 
                    dismissString=kQuitWithoutSave 
                )

        # check to see if user wants to save current scene
        if cmds.about(batch=True) or saveRequest == kSaveAndQuit:
            cmds.file(save=True, force=True)
            retStatus = 20

        # check for batch mode where we don't have UI we automatically save the file.
        if cmds.about(batch=True):
           cmds.warning("Autodesk.MayaScanner : Batch mode : Found corrupted scene, attempted to fixed. Please check userSetup.%s and scene scriptNodes"  % typeExtension)


        # in all cases if errors time to exit Maya
        cmds.quit(force=True, exitCode=retStatus, abort=True)

    else:
        om.MGlobal.displayInfo("Autodesk.MayaScanner : Scan completed: no issues found")


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# command
class MayaScannerCmd(om.MPxCommand):
    kPluginCmdName = "MayaScan"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._clear()

    def _clear(self):
        #local data
        self._scanType = 0

    @staticmethod
    def cmdCreator():
        return MayaScannerCmd()

    def parseArguments(self, args):
        ''' 
        parse the command arguments  
        '''
        
        # The following MArgParser object allows you to check if specific flags are set.
        argData = om.MArgParser( self.syntax(), args )
        
        if argData.isFlagSet( kScanTypeFlag ):
            self._scanType = argData.flagArgumentInt( kScanTypeFlag, 0 )
            
        if argData.isFlagSet( kScanTypeLongFlag ):
            self._scanType = argData.flagArgumentInt( kScanTypeLongFlag, 0 )



    def doIt(self, args):
        # parse arguments to see if given command,  current, file, directory
        # if None given run command on current scene, 
        # else launch file browser to find file or directory name
        # if File load file run scanner, save file
        # if Directory, travse the directory tree load file, scan, save repeat

        # parse command arguments to know what type of scan to do
        self.parseArguments( args )

        # starting a new scan
        issuesFound = 0    
        issuesFixed = 0
        sceneFileSaved = 0
        quitRequest = 0

        reportIssue('reset',1)
        userConfirmFix('reset', '', 1)

        if os.path.exists(MayaScannerLogFile()):
            rollOverLogFile()

        # check to see what was passed as Type, 0=current, 1=file, 2=directory
        # check current file
        if self._scanType == 0:
            issuesFound, issuesFixed, malType = clean_malware('current scene')
      
        # check for new file, prompt for file name to load
        actionTitle = ["", "Choose file to scan", "Choose directory to scan"]

        if self._scanType >= 1:

            fileName = getReadFileName(actionTitle[self._scanType], self._scanType, '*.ma;;*.mb')
     
            #did the user press cancel ?
            if fileName is None:
                om.MGlobal.displayInfo(u'Scan Cancelled')
            else:
                if self._scanType == 1:
                    cmds.file(fileName, open=True, force=True)
                    issuesFound, issuesFixed, malType = clean_malware('fileOpen')

        # end of scanning output summary
        endScanSummary(issuesFound, issuesFixed, malType )


def getReadFileName(message, scanType, fileFilter=''):
    fileName = cmds.fileDialog2(dialogStyle=2, fm=scanType, fileFilter=fileFilter, caption=message, okCaption="Scan")
    if not((fileName is None) or (len(fileName[0]) == 0)):
        fileName = fileName[0]
        fileName = fileName and os.path.normpath(fileName) #hoping this fixes the file path on PCs
        return fileName
    
    return None


def syntaxCreator():
    ''' Define argument flag syntax  '''
    
    syntax = om.MSyntax()

    # flag will be expecting a numeric value, denoted by OpenMaya.MSyntax.kDouble
    syntax.addFlag( kScanTypeFlag, kScanTypeLongFlag, om.MSyntax.kDouble )

    return syntax


# Initialize the plug-in
def initializePlugin(plugin):
    pluginFn = FnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            MayaScannerCmd.kPluginCmdName, MayaScannerCmd.cmdCreator, syntaxCreator)

        # create a menu item - need to add checks for GUI...
        # for now use Mel - rework for pure python scripted plugin
        if not cmds.about(batch=True):
            mel.eval("evalDeferred(\"source ScanMenu.mel; addMenuItemSafe($gMainFileMenu, \\\"AddScanMenuItems\\\", \\\"gScanMenuVariable\\\")\")")  

    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % MayaScannerCmd.kPluginCmdName

        )
        raise


# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = FnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(MayaScannerCmd.kPluginCmdName)
        if not cmds.about(batch=True):
            mel.eval("RemoveScanMenuItems()")
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % MayaScannerCmd.kPluginCmdName
        )
        raise


#-
# ==========================================================================
# Copyright (C) 2020 Autodesk, Inc. and/or its licensors.  All 
# rights reserved.
#
# The coded instructions, statements, computer programs, and/or related 
# material (collectively the "Data") in these files contain unpublished 
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its 
# licensors, which is protected by U.S. and Canadian federal copyright 
# law and by international treaties.
#
# The Data is provided for use exclusively by You. You have the right 
# to use, modify, and incorporate this Data into other products for 
# purposes authorized by the Autodesk software license agreement, 
# without fee.
#
# The copyright notices in the Software and this entire statement, 
# including the above license grant, this restriction and the 
# following disclaimer, must be included in all copies of the 
# Software, in whole or in part, and all derivative works of 
# the Software, unless such copies or derivative works are solely 
# in the form of machine-executable object code generated by a 
# source language processor.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. 
# AUTODESK DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED 
# WARRANTIES INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF 
# NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR 
# PURPOSE, OR ARISING FROM A COURSE OF DEALING, USAGE, OR 
# TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS LICENSORS 
# BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL, 
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK 
# AND/OR ITS LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY 
# OR PROBABILITY OF SUCH DAMAGES.
#
# ==========================================================================
#+
