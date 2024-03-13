
##########
# scan code based on Red9 Consultancy script
##########

'''
    Malware fixer for a known Maya virus discovered in a client file, and were
    subsequently infected with for a few days. The Malware is basically a scriptNode 
    in a scene which auto-generates a userSetup.mel, various mel globals and a scriptJob.
    These are all designed to propagate the scriptNodes in all future files worked on
    within an infected machine.
    
    The ultimate aim of this malware seems to be to hang all Maya files and systems on, or after the 26/06/2020

    Original Author: Mark Jackson
    email: info@red9consultancy.com
    Red9 : http://red9consultancy.com
    Red9 Vimeo : https://vimeo.com/user9491246
    
    to run import this module and run
    clean_malware()

'''


import sys
import os
import logging
import logging.handlers
import tempfile
import fnmatch

import maya.cmds as cmds
import maya.mel as mel

from stat import S_IWUSR, S_IREAD
from MayaScannerUtils import MsgFormat


# create a log file of found issues
def MayaScannerLogFile():
    return os.path.join(tempfile.gettempdir(), "MayaScannerLog.txt")



logging.basicConfig()
log = logging.getLogger('Autodesk.MayaScanner')


if not len(log.handlers):
    filehandler = logging.handlers.RotatingFileHandler(MayaScannerLogFile(), mode='a', backupCount=1, delay=True)
    log.addHandler(filehandler)

# roll over the log file 
def rollOverLogFile():
    log.handlers[0].doRollover()

# ask user if ok to attempt to fix the issue

def userConfirmFix(dlgTitle, msgString, smode=0):

    if 'state' not in userConfirmFix.__dict__:
        userConfirmFix.state = 0
    if smode == 1:
        userConfirmFix.state = 0
        return 0

    if userConfirmFix.state == 0:
        # check with user to continue with attempted fix
        answer = cmds.confirmDialog( title=dlgTitle, message=MsgFormat(msgString+'<br>Attempt to fix issue?'),
               button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if cmds.about(batch=True) or answer == 'Yes':
           userConfirmFix.state = 1

    # return status of user choice 
    return userConfirmFix.state


def reportIssue(msgString, smode=0):

    if 'cnt' not in reportIssue.__dict__:
        reportIssue.cnt = 0
    if smode == 1:
        reportIssue.cnt = 0 
        return
    first = (reportIssue.cnt == 0)
    reportIssue.cnt = 1

    if first:
        log.info("checking issues in file: %s" % cmds.file(q=True, sn=True) )

    log.info(msgString)


def test_ConcreteScriptFiles():
    '''
    test if the userSetup.mel has been created, or appended by the malware
    '''
    prefs = os.path.dirname(os.path.dirname(cmds.about(env=True)))
    usersetups = []
    malType = 0
    status = ''
    testedFilePath = os.path.normpath(os.path.join(prefs, 'scripts', 'userSetup.mel'))
    if os.path.exists(testedFilePath):
        f = open(testedFilePath, "r")
        data = f.read()
        f.close()

        if 'fuck_All_U' in data:
            status = 'compromised'
            reportIssue('userSetup.mel : Compromised by Malware!')
        if all([len(data) >= 4118,
                '// Maya Mel UI Configuration File.Maya Mel UI Configuration File..\n// \n//\n//  This script is machine generated.  Edit at your own risk' in data,
                'string $chengxu' in data]):
            reportIssue('userSetup.mel : Infected by Malware!')
            status = 'rename'
            usersetups.append(testedFilePath)
            malType = 1

    testedFilePath = os.path.normpath(os.path.join(prefs, 'scripts', 'userSetup.py'))
    if os.path.exists(testedFilePath):
        f = open(testedFilePath, "r")
        data = f.read()
        f.close()

        if "cmds.evalDeferred(\'leukocyte = vaccine.phage()\')" in data and "cmds.evalDeferred(\'leukocyte.occupation()\')" in data:
            reportIssue('userSetup.py : Infected by Malware!')
            status = 'rename'
            usersetups.append(testedFilePath)
            malType += 2

    testedFilePath = os.path.normpath(os.path.join(prefs, 'scripts', 'vaccine.py'))
    if os.path.exists(testedFilePath):
        f = open(testedFilePath, "r")
        data = f.read()
        f.close()
        msg = 'vaccine.py found : Unable to assess if it is really infected. Please verify manually.'
        
        if "petri_dish_path = cmds.internalVar(userAppDir=True) + 'scripts/userSetup.py" in data:
            msg = 'vaccine.py found : Infected by Malware!'

        # the vaccine.py content may not contain the 'petri_dish_path' pattern. This may occur if the python interpreter
        # raised an exception during the evaluation and the file has not been fully written. Typically, Python 3 can
        # except with the following:
        #
        # # UnicodeEncodeError: 'charmap' codec can't encode characters in position 51-52: character maps to <undefined>
        #
        # But any other 'error' cause, may write 'vaccine.py' with partial content or no content at all. Although
        # in this case the file is not, technically, infected, we still rename it!

        reportIssue(msg)
        status = 'rename'
        usersetups.append(testedFilePath)

    return usersetups, status, malType

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def fix_userSetup(prefixTitle, smode):
    issueFound = 0
    issueFixed = 0
    usersetups, status, malwareType = test_ConcreteScriptFiles()
    if status == 'rename':
        # found an issue notifiy user, ask to attempt fix
        if userConfirmFix('Autodesk.MayaScanner: %s : ' % prefixTitle, 'Found corrupted userSetup file(s)', smode):
            for usersetup in usersetups:
                # we still want to know of this for fail report
                issueFound += 1
                #
                os.chmod(usersetup, S_IWUSR | S_IREAD)
                try:
                    pyCache = os.path.join(os.path.dirname(usersetup),'__pycache__')
                    if os.path.exists(pyCache):
                        findvaccine = find('vaccine*', pyCache)
                        for vacPath in findvaccine:
                            os.remove(vacPath)
                            reportIssue('Pyc vaccine file : %s has deleted' % vacPath)
                    if os.path.exists(usersetup + '.INFECTED') == True:
                        os.remove(usersetup + '.INFECTED')
                        reportIssue('Previous infected file : %s has deleted' % usersetup + '.INFECTED')

                    os.rename(usersetup, usersetup + '.INFECTED')
                    issueFixed += 1
                    reportIssue('Renamed : %s' % usersetup)
                except:
                    reportIssue("Can't rename %s file" % usersetup)

    return issueFound, issueFixed, malwareType

def test_scriptNodes():
    '''
    test for the known scriptNode with specific data
    '''
    malware_scripts = []
    for script in cmds.ls(type='script'):
        if 'MayaMelUIConfigurationFile' in script.split('|')[-1].split(':')[-1]:
            scriptdata = cmds.scriptNode(script, bs=True, q=True)
            if 'This script is machine generated.  Edit at your own risk' in scriptdata and 'fuck_All_U' in scriptdata:
                malware_scripts.append(script)
                reportIssue('scriptNode present : %s' % script)
        if 'vaccine_gene' in script or 'breed_gene' in script:
            malware_scripts.append(script)
            reportIssue('scriptNode present : %s' % script)

    return malware_scripts

def fix_scriptNodes(prefixTitle, smode):
    issueFound = 0
    issueFixed = 0
    for script in test_scriptNodes():
        if userConfirmFix('Autodesk.MayaScanner: %s : ' % prefixTitle, 'Found corrupted scriptNode', smode ):
          cmds.delete(script)
          reportIssue('Removed : scriptNode: %s' % script)
          issueFixed += 1
        issueFound += 1

    return issueFound, issueFixed

def test_scriptJob():
    '''
    test for the scriptJob this Malware geenerates
    '''
    scriptjob_id = []
    try:
        a = -1
        if (mel.eval('whatIs "$autoUpdateAttrEd_aoto_int"') != "Unknown"):
            a = int(mel.eval('$temp=$autoUpdateAttrEd_aoto_int'))
        for jobStr in cmds.scriptJob(listJobs=True):
            if jobStr.startswith(str(a)) == True:
                scriptjob_id.append(a)
                reportIssue('Malware 1: scriptJob present : %s' % a)
            # find Malware 2
            if 'leukocyte.antivirus()' in jobStr:
                foundId = jobStr.split(":")[0]
                if foundId.isdigit():
                    scriptjob_id.append(int(foundId))
                    reportIssue('Malware : scriptJob present : %s' % foundId)
    except:
        reportIssue('scriptjob not found')
    return scriptjob_id

def fix_scriptJob(prefixTitle, smode):
    issueFound = 0
    issueFixed = 0
    ids = test_scriptJob()
    for foundId in ids:
        if userConfirmFix('Autodesk.MayaScanner: %s : ' % prefixTitle, 'Found corrupted scriptJob', smode):
            cmds.scriptJob(kill=foundId, force=True)
            reportIssue('Removed : scriptJob ID: %s' % str(foundId))
            issueFixed += 1
        issueFound += 1

    return issueFound, issueFixed

#
# script to run, would like to know if running single file or multiple for file logging
def clean_malware(prefixTitle, dontPrompt=False):
    '''
    remove the damn thing and all nodes created!
    '''

    # first kill the mel globals!
    mel_globals = ['UI_Mel_Configuration_think',
                   'UI_Mel_Configuration_think_a',
                   'UI_Mel_Configuration_think_b',
                   'autoUpdateAttrEd_SelectSystem',
                   'autoUpdatcAttrEd',
                   'autoUpdatoAttrEnd']
    for glb in mel_globals:
        if mel.eval('whatIs("%s")' % glb) == 'Mel procedure entered interactively.':
            mel.eval('global proc %s(){error -sl "attempted to run corrupted command: %s";}' % (glb,glb))

    # run the base fixes
    issuesFound = 0
    issuesFixed = 0

    sJobFound, sJobFixed     = fix_scriptJob(prefixTitle, int(dontPrompt))
    sNodeFound, sNodeFixed   = fix_scriptNodes(prefixTitle, int(dontPrompt))
    sSetupFound, sSetupFixed, malType = fix_userSetup(prefixTitle, int(dontPrompt))
    
    issuesFound = sJobFound + sNodeFound + sSetupFound
    issuesFixed = sJobFixed + sNodeFixed + sSetupFixed

    return issuesFound, issuesFixed, malType


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
