import sublime
import sublime_plugin
import re
import os
import fnmatch

pathSlash ='/' if sublime.platform()!='windows' else '\\'

class SassSolutionCommand(sublime_plugin.EventListener):
    def on_post_save(self, view):        
        Engine.runEngine(self,view)

    def on_query_completions(self, view, prefix, locations):

        isSass = view.match_selector(locations[0], 'source.scss')
        if isSass:
            return Engine.completionList




class AddToAutoCompleteCommand(sublime_plugin.WindowCommand):
    def run(self,paths=[]):

        for x in paths:
            if os.path.isfile(x):
                filesList=Engine.getFiles()
                filesList.append(x+pathSlash)
                Engine.setFiles(filesList)
            else:                
                foldersList=Engine.getFolders()
                foldersList.append(x+pathSlash)
                Engine.setFolders(foldersList)

        Engine.saveSettings()


class RemoveFromAutoCompleteCommand(sublime_plugin.WindowCommand):
    def run(self,paths=[]):

        for x in paths:
            settingsList=Engine.getFiles() if os.path.isfile(x) else Engine.getFiles()
            settingsList.remove(x) 
            Engine.loadSettings().set()

        Engine.saveSettings()


class ClearAutoCompleteCommand(sublime_plugin.WindowCommand):
    def run(self,paths=[]):
        Engine.eraseFiles()
        Engine.eraseFolders()
        Engine.saveSettings()
class Engine:
    completionList=[]

    def isSass(myview):
        extension='.scss'

        if(isinstance(myview,sublime.View)):
            return myview.file_name().endswith(extension)
        else:
            return myview.endswith(extension)


    def loadSettings():
        return sublime.load_settings('sassSolution.sublime-settings')


    def saveSettings():
        sublime.save_settings('sassSolution.sublime-settings')


    def getFolders():
        return Engine.loadSettings().get('folders')


    def getFiles():
        return Engine.loadSettings().get('files')


    def setFolders(newList):
        Engine.loadSettings().set('folders',newList)


    def setFiles(newList):
        Engine.loadSettings().set('files',newList)


    def eraseFiles():
        Engine.loadSettings().erase('files');


    def eraseFolders():
        Engine.loadSettings().erase('folders');


    def getFoldersFilesRecursively(folder):
        matches=[]

        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.scss'):
                matches.append(os.path.join(root, filename))

        return matches


    def filterFilesAndFoldersToCurrentProject(folders,files,view):
        currentProjectPath=view.window().folders()[0];

        filteredFolders = [folder for folder in folders if currentProjectPath in folder]
        filteredFiles = [file for file in files if currentProjectPath in file]

        return (filteredFolders,filteredFiles)


    def getFilesAndFoldersText(folders,files,view):
        folders,files=Engine.filterFilesAndFoldersToCurrentProject(folders,files,view)
        code=''

        for x in folders:
            for file in Engine.getFoldersFilesRecursively(x):
                code+=open(file,'r', encoding="utf8").read()

        for x in files:
            code+=open(x,'r' ,encoding="utf8").read()

        return code


    def writeJsonFile(content):
        path=sublime.packages_path()+pathSlash+'User'+pathSlash+'sbc-api-mysass.sublime-settings'
        f=open(path,'w',encoding="utf8")

        contents = "".join(content)
        f.write(contents)
        f.close()


    def escapeDollar(text,replaceDollar=True):
        return text.replace('$','\$' if replaceDollar else '$')


    def addMixinsCompletion(pattern,code):
        mixinsCompletion=[]

        for x in re.findall(pattern,code):
            mixinName=Engine.escapeDollar(x[0])
            mixinArguments=Engine.escapeDollar(x[2])

            zeroSlashesMixinArguments=Engine.removeDollarSlashes(mixinArguments)

            mixinsCompletion.append((mixinName+'('+zeroSlashesMixinArguments+')','@include '+mixinName+'('+mixinArguments+')'))

        return mixinsCompletion


    def addVariablesCompletion(pattern,code):
        variablesCompletion=[]

        for x in re.findall(pattern,code):
            variableName=Engine.escapeDollar(x[0])
            variableValue=Engine.escapeDollar(x[1],False)

            variablesCompletion.append(('$'+variableName+'\t'+variableValue,'\$'+variableName))

        return variablesCompletion


    def removeDollarSlashes(text):
        return text.replace('\\','')


    def runEngine(self,view):
        if Engine.isSass(view):
                Engine.completionList=[]
                allSass=Engine.getFilesAndFoldersText(Engine.getFolders(),Engine.getFiles(),view)

                Engine.completionList+=Engine.addVariablesCompletion(r'\$([\w*-]*):(.*?);',allSass)
                Engine.completionList+=Engine.addMixinsCompletion('\@mixin ([\w*-]*)\s{0,}(\((.*?)\)|{|\n)',allSass)