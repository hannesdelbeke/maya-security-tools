########################################################################
# DESCRIPTION:
#
# Produces the command "MayaScannerCB". 
#
# To use, make sure that MayaScannerCB.py is in your MAYA_PLUG_IN_PATH,
# then do the following:
#
#    import maya
#    maya.cmds.loadPlugin("MayaScannerCB.py")
#    maya.cmds.MayaScannerCB()
#
########################################################################

import sys
import os
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import maya.OpenMaya as OpenMaya

from MayaScannerCleaner import clean_malware, userConfirmFix
from MayaScannerUtils import FnPlugin, MsgFormat


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


MayaScannerCB_cbIds = []
MayaScannerCB_result = 0

# command
class MayaScannerCBcmd(om.MPxCommand):
    kPluginCmdName = "MayaScannerCB"
    referencedFiles = []

    mayaFile = {
        'Open'            : "",
        'Import'          : "",
        'LoadReference'   : [],
        'ImportReference' : []
        }

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return MayaScannerCBcmd()

    def doIt(self, args):
        if MayaScannerCB_result != 0:
           cmds.error("Autodesk.MayaScannerCB  : FileCallack : issues have been detected")
        return MayaScannerCB_result

    @staticmethod
    def setFileName(clientData, fileName):
        """
        Fill the MayaScannerCBcmd.mayaFile dictionary entry based on the clientData
        """
        index = clientData.replace('before', '')
        if index == clientData:
            index = clientData.replace('after', '')

        # to keep track of recursive References, we push to the array
        if index in ['LoadReference', 'ImportReference']:
            MayaScannerCBcmd.mayaFile[index].append(fileName)
        else:
            MayaScannerCBcmd.mayaFile[index] = fileName

    @staticmethod
    def getFileName(clientData):
        """
        Get the MayaScannerCBcmd.mayaFile dictionary entry based on the clientData
        """
        index = clientData.replace('after', '')
        if index == clientData:
            index = clientData.replace('before', '')
         
        # to keep track of recursive References, we pop from the array at each call.
        # Note that this approach works because there is only one call of this function
        # in the MayaScanAfterCB
        if index in ['LoadReference', 'ImportReference']:
            return MayaScannerCBcmd.mayaFile[index].pop()
        else:
            return MayaScannerCBcmd.mayaFile[index]

    @staticmethod
    def UpdateReferencesList(fileName, corrupted, isRef):
        """
        Check if we need to remove fileName from MayaScannerCBcmd.referencedFiles
        """
        if not corrupted and isRef:
            # remove fileName from the list since it has been reported as 'not corrupted'
            # and we don't want to display it in the dialog.
            
            # Just in case fileName is not in the list, let's ignore the raised exception
            try:
                MayaScannerCBcmd.referencedFiles.remove(fileName)
            except ValueError:
                sys.stderr.write("trying to remove unknown element(%s) from list\n" % fileName)

    @staticmethod
    def MayaScanBeforeCB(clientData):
        # This callback is only used to remember the Maya file name in case it gets cleared because
        # of reading errors so the call 'cmds.file(q=True, sn=True)' would not be able to return a
        # meaningful value
        if clientData == 'beforeOpen':
            # when running in Python 2.x, the list does not defines 'clear'
            if sys.version_info[0] < 3:
                MayaScannerCBcmd.referencedFiles[:] = []
            else:
                MayaScannerCBcmd.referencedFiles.clear()
            MayaScannerCBcmd.setFileName(clientData, OpenMaya.MFileIO.beforeOpenFilename())
        elif clientData == 'beforeImport':
            # when running in Python 2.x, the list does not defines 'clear'
            if sys.version_info[0] < 3:
                MayaScannerCBcmd.referencedFiles[:] = []
            else:
                MayaScannerCBcmd.referencedFiles.clear()
            MayaScannerCBcmd.setFileName(clientData, OpenMaya.MFileIO.beforeImportFilename())
        elif clientData == 'beforeLoadReference' or clientData == 'beforeImportReference':
            fname = OpenMaya.MFileIO.beforeReferenceFilename()
            MayaScannerCBcmd.setFileName(clientData, fname)
            if fname not in MayaScannerCBcmd.referencedFiles:
                MayaScannerCBcmd.referencedFiles.append(fname)
        
    @staticmethod
    def MayaScanAfterCB(clientData):
        kSaveAndQuit     = 'Save and Quit'
        kQuitWithoutSave = 'Quit without Saving'
        retStatus = 0    # no issues found

        # get the correct baseName from the fileName dictionary
        fileName = MayaScannerCBcmd.getFileName(clientData)
        mayaBaseName = os.path.basename(fileName)

        # define the QUARANTINED folder where 'fixed' file will be saved. This is only used
        # when 'cmds.file(q=True,sn=True) == ""' because we don't want to overwrite the orinal file (even
        # if it is corrupted) and we are not sure that the original file/path is writeable anyway!
        quarantinedFolder = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(cmds.about(env=True))), 'QUARANTINED'))

        # detect if we are processing a referenced file so we don't 'prompt to fix' inside the clean_malware
        # since, anyway, we can't modify referenced files and user must fix them manually
        referenceLoad = False
        warnCase = 'FileCallback'
        if clientData == 'afterLoadReference' or clientData == 'afterImportReference':
            warnCase = 'ReferenceCallback'
            referenceLoad = True
        elif clientData == 'afterImport' and cmds.file(q=True,sn=True) == "":
            warnCase = 'Import No Scene Name'

        userConfirmFix('reset', '', 1)
        corrupt_found, corrupt_fixed, malType = clean_malware('FileOpenCB', referenceLoad)

        # if the clean_malware detected no corruption, remove mayaBaseName from the References list
        MayaScannerCBcmd.UpdateReferencesList(fileName, corrupt_found, referenceLoad)

        if corrupt_found != 0:
            retStatus = 19        # issues found
            saveRequest = ""
            checkQuarantined = False
            typeExtension = 'mel' if malType == 1 else 'py'
            batchMode = cmds.about(batch=True)
            unnamedScene = cmds.file(q=True,sn=True) == ""
            
            cmds.warning("Autodesk.MayaScannerCB  : %s : detected corrupted scene. Please check scene file '%s'" % (warnCase,mayaBaseName))

            if not referenceLoad:
                # if errors occured while reading the file and we can't get its filename from the
                # 'cmds.file()' command, we use the mayaBaseName instead
                quarantined = os.path.join(quarantinedFolder, mayaBaseName)

                # make sure the QUARANTINED folder exists
                if not os.path.exists(quarantinedFolder):
                    os.makedirs(quarantinedFolder)

                if len(MayaScannerCBcmd.referencedFiles) > 0:
                    # we have a list of corrupted references files. Display info (this is a delayed pop-up because
                    # we want to display it only once with the list of all 'corrupted' references (instead of popping
                    # it for each file)
                    refFiles = '<ul>'
                    for f in MayaScannerCBcmd.referencedFiles:
                        refFiles += '<li>'+os.path.basename(f)+'</li>'
                    refFiles += '</ul>'

                    saveRequest = cmds.confirmDialog( 
                        title='Autodesk.MayaScannerCB', 
                        message=MsgFormat("Found corrupted scene during reference load.<br>" \
                                    "We are unable to clean the referenced file(s):" \
                                    "%s" \
                                    "<br><br>We recommend that you:<ol>" \
                                    "<li><b>Quit</b> Maya.</li>" \
                                    "<li>Load scene(s) separately or fix offline.</li></ol><br>" % refFiles),
                        messageAlign='center',
                        button=[kQuitWithoutSave], 
                        defaultButton=kQuitWithoutSave, 
                        cancelButton=kQuitWithoutSave,
                        dismissString=kQuitWithoutSave
                    )
                    if batchMode and unnamedScene:
                        # rename the current scene
                        cmds.file(rename=quarantined)
                        checkQuarantined = True
                elif unnamedScene:
                    # rename the current scene
                    cmds.file(rename=quarantined)
                    checkQuarantined = True
                    saveRequest = cmds.confirmDialog( 
                        title='Autodesk.MayaScannerCB',
                        message=MsgFormat("Found corrupted scene, No scene name.<br>" \
                                          "Attempting to save to: '%s' before quitting Maya ?" % quarantined),
                        messageAlign='center',
                        button=[kSaveAndQuit, kQuitWithoutSave], 
                        defaultButton=kSaveAndQuit, 
                        cancelButton=kQuitWithoutSave, 
                        dismissString=kQuitWithoutSave
                    )
                else:
                    # should be able to save cases
                    if corrupt_fixed < corrupt_found:
                        saveRequest = cmds.confirmDialog( 
                            title='Autodesk.MayaScannerCB',
                            message=MsgFormat('Found corrupted scene, not fully fixed.<br>' \
                                              'We recommend that you:<ol>' \
                                              '<li><b>Quit</b> Maya.</li>' \
                                              '<li>Check userSetup.%s and scene file scriptNodes.</li>' \
                                              '<li>Start new Maya session.</li></ol><br>' % typeExtension),
                            messageAlign='center',
                            button=[kSaveAndQuit, kQuitWithoutSave], 
                            defaultButton=kQuitWithoutSave, 
                            cancelButton=kQuitWithoutSave, 
                            dismissString=kQuitWithoutSave 
                        )
                    else:
                        saveRequest = cmds.confirmDialog( 
                            title='Autodesk.MayaScannerCB',
                            message=MsgFormat('Found corrupted scene, attempted to fix.<br>' \
                                              'We recommend that you:<ol>' \
                                              '<li><b>Save</b> the current scene.</li>' \
                                              '<li>Quit Maya.</li>' \
                                              '<li>Check userSetup.%s and scene file scriptNodes.</li>' \
                                              '<li>Start new Maya session.</li></ol><br>' % typeExtension),
                            messageAlign='center',
                            button=[kSaveAndQuit, kQuitWithoutSave], 
                            defaultButton=kSaveAndQuit, 
                            cancelButton=kQuitWithoutSave, 
                            dismissString=kQuitWithoutSave
                        )

                # check to see if user wants to save current scene
                if batchMode or saveRequest in [kSaveAndQuit]:
                    cmds.file(save=True, force=True)
                    retStatus = 20          # errors found and saved

                # check for batch mode where we don't have UI.We automatically saved the file.
                if batchMode:
                    msg = "Autodesk.MayaScannerCB : Batch mode : Found corrupted scene, attempted to fix. Please check userSetup.%s" % (typeExtension)
                    if checkQuarantined:
                        msg += ", scene file scriptNodes and '%s' folder." % (quarantinedFolder)
                    else:
                        msg += " and scene file scriptNodes."
                    cmds.warning(msg)

            # quit only if requested
            if saveRequest in [kSaveAndQuit, kQuitWithoutSave]:
                if saveRequest in [kQuitWithoutSave]:
                    # clear the whole scene from memory in case there are locked scriptNodes brought in
                    # by a referenceLoad and that we were unable to clean
                    cmds.file(newFile=True)
                cmds.quit(force=True, exitCode=retStatus, abort=True)

    @staticmethod
    def clearCB():
        if len(MayaScannerCb_cbIds) > 0:
            for id in MayaScannerCB_cbIds:
                om.MMessage.removeCallback(id)


# Initialize the plug-in
def initializePlugin(obj):
    plugin = FnPlugin(obj)
    try:
        plugin.registerCommand(
            MayaScannerCBcmd.kPluginCmdName, MayaScannerCBcmd.creator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % MayaScannerCBcmd.kPluginCmdName
        )
        raise

    # add Before* callbacks so we can get the filename before it gets cleared if errors occurred during the file read pass
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeOpen, MayaScannerCBcmd.MayaScanBeforeCB,'beforeOpen'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeImport, MayaScannerCBcmd.MayaScanBeforeCB,'beforeImport'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeLoadReference, MayaScannerCBcmd.MayaScanBeforeCB,'beforeLoadReference'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeImportReference, MayaScannerCBcmd.MayaScanBeforeCB,'beforeImportReference'))

    # add the After* callbacks to scan the opened file for issues
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, MayaScannerCBcmd.MayaScanAfterCB,'afterOpen'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterImport, MayaScannerCBcmd.MayaScanAfterCB,'afterImport'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterLoadReference, MayaScannerCBcmd.MayaScanAfterCB,'afterLoadReference'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterImportReference, MayaScannerCBcmd.MayaScanAfterCB,'afterImportReference'))

# Uninitialize the plug-in
def uninitializePlugin(obj):
    plugin = FnPlugin(obj)

    for id in MayaScannerCB_cbIds:
        om.MMessage.removeCallback(id)

    try:
        plugin.deregisterCommand(MayaScannerCBcmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % MayaScannerCBcmd.kPluginCmdName
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

