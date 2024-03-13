########################################################################
# DESCRIPTION:
#
# Utility procedures for the "MayaScan" commands.
#
#
########################################################################
import os,re,platform
import maya.api.OpenMaya as om

class MayaScannerUtils():
    kPluginVendor = "Autodesk, Inc."
    kPluginVersion = "Unknown"
    kPluginApiVersion = "Any"

    def __init__(self):
        self._readInfo()

    def _readInfo(self):
        def getValueOf(key, data, default):
            val = default
            pattern = r''+key+'='+'"(.*?)"'
            found = re.findall(pattern, data)
            if found: val = found[0]
            return val

        # read info from PackageContents file if found. If not, keep default values
        location = os.path.dirname(os.path.realpath(__file__))
        packageInfo = os.path.join(location, '..', '..', 'PackageContents.xml')
        if os.path.exists(packageInfo):
            file = open(packageInfo, 'r')
            data = file.read()
            file.close()
            self.kPLuginVendor = getValueOf('Author', data, self.kPluginVendor)
            self.kPluginVersion = getValueOf('AppVersion', data, self.kPluginVersion)

def FnPlugin(plugin):
    utils = MayaScannerUtils()
    return om.MFnPlugin(plugin,
                        vendor=utils.kPluginVendor,
                        version=utils.kPluginVersion,
                        apiVersion=utils.kPluginApiVersion)

# reformat the incoming string for the destination platform.
# The MayaScanner tools seem to be using HTML tags to format the dialogs messages. 
# However, on Windows, these tags are ignored and would result in strange characters
# displayed (or the 2 or more sequential spaces that represent a new line are ignored). 
# This function will take care of these control sequences.
# For now, assuming that both MacOS and Linux support the Markdown syntax
# in their dialogs.
def MsgFormat(string):
    if platform.system()=="Windows" or platform.system() == "Microsoft":
        string = string.replace('  '   , '\n')
        string = string.replace('<br>' , '\n')
        string = string.replace('<b>'  , '')
        string = string.replace('</b>' , '')
        string = string.replace('<ol>' , '\n')
        string = string.replace('</ol>', '')
        string = string.replace('<ul>' , '\n')
        string = string.replace('</ul>', '')
        string = string.replace('<li>' , '  - ')
        string = string.replace('</li>', '\n')
    return string
