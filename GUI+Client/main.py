from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.logger import Logger
from kivy.logger import LoggerHistory
from kivy.config import Config
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
#Changes the window size
#from kivy.core.window import Window
#import kivy.metrics
#Window.size = (kivy.metrics.mm(72.3), kivy.metrics.mm(157.8)) #Height, Width
#MAC
import subprocess
import os
from pathlib import Path
import time
import datetime
import sys
#Regular Expressions
import re
#Client
import client
#network interfaces
import netifaces
import threading

"""
License:

   Copyright 2020 Ryan Wang and Tyllis Xu

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

#Creates a .CovidContactTracer directory to store logs and local files
#First step to create logs
this = sys.modules[__name__]
if platform != 'android':
    if os.path.isdir(Path.home()):
        #A file exists
        this.appPath = str(Path.home()) + os.sep + '.CovidContactTracer'
        if not os.path.isdir(this.appPath):
            #Makes the directory where log files will be at
            os.mkdir(this.appPath)
    else:
        #Throw error
        raise OSError
else:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET])
    this.appPath = ""
#Logging settings
this.versionNumber = '1.0.0'
this.logVerbosity = 20
this.storeName = 'local'
this.deleteAllData = False
if this.logVerbosity < 10:
    
    this.log_level = "trace"
elif this.logVerbosity < 20:
    
    this.log_level = "debug"
elif this.logVerbosity < 30:
    
    this.log_level = "info"
    
    
elif this.logVerbosity < 40:
    
    this.log_level = "warn"
elif this.logVerbosity < 50:
    
    this.log_level = "error"
    #Usually used for debugging
elif this.logVerbosity == 50:
    
    this.log_level = "critical"
else:
    this.log_level = "trace"
Config.set('kivy', 'log_level', this.log_level)
if this.appPath == "":
    
    Config.set('kivy', 'log_dir', this.appPath)
    
    
Config.set('kivy', 'log_name', "CovidContactTracerGUI_%y-%m-%d_%_.log")
Config.set('kivy', 'log_maxfiles', 49)
Config.write()

#Memory storage class for when the app is running.
class storageUnit():

    def __init__(self):
        #Creates instance
        Logger.info('creating an instance of storageUnit')

    #Adds a unknown / new mac address that was not on the previous network into the json file
    def addEntry(self, macAddress, time):
        pauseThread(this.myClockThread)
        if macAddress in this.store.get("macDict")["value"]:
            tempNewMacDict = this.store.get("macDict")["value"]
            
            
            tempNewMacDict[macAddress] = time
            this.store.put("macDict", value = tempNewMacDict)
            
            tempNewMacDict = 0

            tempNewRecentTen = this.store.get("recentTen")["value"]
            tempNewRecentTen = [[time, macAddress]] + tempNewRecentTen[:9]
            #This stores the recent Ten
            this.store.put("recentTen", value = tempNewRecentTen)
            
            #This point is when addEntry has been updated
            tempNewRecentTen = 0
            Logger.info('addEntry updated ' + macAddress + ' met at '+time)
        else:
            tempNewNumEntries = this.store.get("numEntries")["value"]
            
            tempNewNumEntries += 1
            
            
            this.store.put("numEntries", value = tempNewNumEntries)
            tempNewNumEntries = 0

            tempNewMacDict = this.store.get("macDict")["value"]
            tempNewMacDict[macAddress] = time
            #Time is added
            this.store.put("macDict", value = tempNewMacDict)
            
            
            tempNewMacDict = 0

            tempNewRecentTen = this.store.get("recentTen")["value"]
            tempNewRecentTen = [[time, macAddress]] + tempNewRecentTen[:9]
            #Recent ten appended
            this.store.put("recentTen", value = tempNewRecentTen)
            tempNewRecentTen = 0

            Logger.info('addEntry added ' + macAddress + ' met at '+time)
            
        resumeThread(this.myClockThread)
        #The thread is resumed, meaning that the clock is starting to count again


    #Checks if the previous prevNetwork is the same as foreignSet, which is a set
    def isSamePrevNetwork(self, foreignSet):
        returnArr = []
        
        for i in foreignSet:
            
            
            if i not in this.store.get("prevNetwork")["value"]:
                returnArr += [i]
        Logger.info('isSamePrevNetwork filtered ' + repr(foreignSet) + ' into ' + repr(returnArr))
        return returnArr


#Class that collects Mac Addresses
class GetMacAdd():
    def __init__(self, **kwargs):
        self.storage = storageUnit()

        self.supported = None  #  Documents whether our mac address collection method is supported
        Logger.info('creating an instance of GetMacAdd')

    #Function that converts the recentTen list to a string (For storage in JSON)
    def getString(self, recentTen):
        returnStr = ""
        for i in recentTen:
            returnStr += repr(i)+ "\n"
        Logger.info('getString returned ' + repr(returnStr) + ' from input ' + repr(recentTen))
        return returnStr


    #Gets own self device mac address
    def getMacSelf(self):
        selfMac = []
        isContractionStart = re.compile(r'^([\da-fA-F]):')
        isContractionMid = re.compile(r':([\da-fA-F]):')
        
        
        isContractionEnd = re.compile(r':([\da-fA-F])$')
        
        for interface in netifaces.interfaces():
            Logger.info('getMacSelf checking interface ' + interface)
            try:
                mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
                Logger.info('getMacSelf:' + interface + ' has MAC addr ' + mac)
                if re.search(isContractionStart,mac) is not None:
                    digit = re.search(isContractionStart,mac).group(1)
                    mac = re.sub(isContractionStart,digit + "0:",mac)
                if re.search(isContractionEnd,mac) is not None:
                    digit = re.search(isContractionEnd,mac).group(1)
                    mac = re.sub(isContractionEnd,":" + digit + "0",mac)
                while re.search(isContractionMid,mac) is not None:
                    digit = re.search(isContractionMid,mac).group(1)
                    mac = re.sub(isContractionMid,":" + digit + "0:",mac)
                if  re.match(r'00[:0]*', mac) is None:
                    selfMac.append(mac)
                    Logger.info('getMacSelf:' + mac + ' has been appended to output of function')
            except KeyError:
                pass
            except ValueError:
                pass

        if selfMac == []:
            raise OSError
        else:
            Logger.info('getMacSelf returned ' + str(selfMac))
            return selfMac
    #Method that gets the mac address. Returns the previous (current) network mac address
    def getMac(self):
        macInitStr = self.tryGetMac()
        
        
        Logger.debug("We have entered getMac")
        macInitStr = repr(macInitStr)
        #This debugs the code by getting getMac and recording into directory folder
        Logger.debug('getMac: recieved ' + macInitStr)
        
        
        isMacAddr = re.compile(r"([\da-fA-F]{1,2}:[\da-fA-F]{1,2}:[\da-fA-F]{1,2}:[\da-fA-F]{1,2}:[\da-fA-F]{1,2}:[\da-fA-F]{1,2})")
        isFloodAddr = re.compile("FF:FF:FF:FF:FF:FF",re.I)
        shortMacList = re.findall(isMacAddr,macInitStr)
        isContractionStart = re.compile(r'^([\da-fA-F]):')
        isContractionMid = re.compile(r':([\da-fA-F]):')
        isContractionEnd = re.compile(r':([\da-fA-F])$')
        macList = []
        for mac in shortMacList:
            if re.search(isContractionStart,mac) is not None:
                digit = re.search(isContractionStart,mac).group(1)
                mac = re.sub(isContractionStart,digit + "0:",mac)
            if re.search(isContractionEnd,mac) is not None:
                
                
                digit = re.search(isContractionEnd,mac).group(1)
                mac = re.sub(isContractionEnd,":" + digit + "0",mac)
            while re.search(isContractionMid,mac) is not None:
                digit = re.search(isContractionMid,mac).group(1)
                
                mac = re.sub(isContractionMid,":" + digit + "0:",mac)
                
            if re.search(isFloodAddr,mac) is None:
                macList.append(mac)

        Logger.debug('getMac: filtered into ' + repr(macList))

        #macList is the list of mac addresses that was returned by the arp-a
        compareSet = set(macList)
        diffArr = self.storage.isSamePrevNetwork(compareSet)
        if len(diffArr) == 0:
            Logger.debug('getMac: No new MAC Addr found')
            #This means that the previous network is the same as the current network
            return self.getString(this.store.get("prevNetwork")["value"])
        else:
            #Appends on a new mac address if it does not exist
            for macAdd in diffArr:
                self.storage.addEntry(macAdd, datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
            pauseThread(this.myClockThread)
            this.store.put("prevNetwork", value = dict.fromkeys(compareSet, 0))
            resumeThread(this.myClockThread)
            return self.getString(this.store.get("prevNetwork")["value"])

    #Method that attempts to arp the mac address. If not, logger records a critical message
    def tryGetMac(self):
        Logger.debug("We have entered tryGetMac")
        fails = 0
        if os.path.isfile(os.sep+"proc"+os.sep+"net"+os.sep+"arp"):
            if os.access(os.sep+"proc"+os.sep+"net"+os.sep+"arp", os.R_OK):
                f=open(os.sep+"proc"+os.sep+"net"+os.sep+"arp", "r")
                result = f.read()
                self.supported = True  #  Documents whether our mac address collection method is supported
                Logger.info('tryGetMac: read proc/net/arp successfully and got ' + result)
                return result
            else:
                Logger.warning("read /proc/net/arp failed")
                fails = fails + 1
        else:
            fails = fails + 1
            Logger.warning("read /proc/net/arp failed")
        if platform != 'android':
            try:
                result = subprocess.run(['arp', '-a'], stdout=subprocess.PIPE)
                self.supported = True #  Documents whether our mac address collection method is supported
                Logger.info('tryGetMac: executed arp -a successfully and got ' + repr(result))
                return result
            except subprocess.CalledProcessError:
                fails = fails + 1
                Logger.warning("arp -a failed")
                pass
        else:
            fails = fails + 1
        self.supported = False #  Documents whether our mac address collection method is supported
        Logger.critical('tryGetMac: all MAC address scanning methods failed')
        return ""


    


class clockThread():
    def __init__(self, runInterval):
        #Threading is used for preventing the code from overwriting storage
        self.enabled = True
        self.running = True
        self.runInterval = runInterval
        self._thread = threading.Thread(target=self.thread_func, args=())
        self._thread.start()
        self.macGenerator = GetMacAdd()
        

    def thread_func(self):
        while self.enabled:
            for index in range(self.runInterval):
                while not self.running and self.enabled:
                    time.sleep(1)
                if self.enabled:
                    time.sleep(1)
                else:
                    Logger.info("Thread Killed")
                    break
            if self.enabled:
                self.macGenerator.getMac()
#Reference / Creates JSON file in .CovidContactTracer

if this.appPath != "":
    this.store = JsonStore(this.appPath + os.sep + this.storeName + '.json')
    this.myClockThread = clockThread(600)
else:
    this.store = JsonStore('local.json')
    this.myClockThread = clockThread(600)


#Method that checks internet connection. Returns False if no internet
def isInternet():
    if client.testInternetConnection():
        Logger.info("Internet connection acheived")
        return True
    else:
        Logger.warning("No internet connection to server. ")
        return False

#Class that defines the error popup page
def showError():
    show = ErrorPopup()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopup(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorServer():
    show = ErrorPopupServer()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupServer(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorSecret():
    show = ErrorPopupSecret()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupSecret(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorMAC():
    show = ErrorPopupMAC()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupMAC(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorTime():
    show = ErrorPopupTime()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupTime(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorCSV():
    show = ErrorPopupCSV()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupCSV(Screen, FloatLayout):
    pass


#Class that defines the error popup page
def showErrorActualTime(allowedTime):
    show = ErrorPopupActualTime()
    popupWindow = Popup(title="Next check Allowed : " + str(allowedTime), content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupActualTime(Screen, FloatLayout):
    pass


#Class that defines the error popup page
def showErrorCatchAll():
    show = ErrorPopupCatchAll()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupCatchAll(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorInternet():
    show = ErrorPopupInternet()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupInternet(Screen, FloatLayout):
    pass

#Class that defines the error popup page
def showErrorLogic():
    show = ErrorPopupLogic()
    popupWindow = Popup(title="Error! ", content=show,size_hint=(0.65, 0.65), pos_hint={"center_x":0.5, "center_y": 0.5})
    popupWindow.open()


#Class that formats the error popup page
class ErrorPopupLogic(Screen, FloatLayout):
    pass


#Class for the homepage screen
class HomePage(Screen, Widget):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)
        #Store for all the permanent storage
        self.store = this.store
        #variable used to reference the getMac class to arp for surrounding MAC addresses
        self.macClass = GetMacAdd()
        #Variable used to record your own personal macAddress
        self.selfMacAddress = self.macClass.getMacSelf()[0]
        Logger.info('creating an instance of HomePage')
        #Determines if the server initiation is correct (should only be a one time boolean)
        isSuccessful = True

        client.init(this.appPath, this.logVerbosity)
        #Variable that stores what the status is for the user. This is just initialization
        self.statusLabel = ObjectProperty(None)
        #Variable that stores what the mac addresses are printed on. This is just initialization
        self.macDisplay = ObjectProperty(None)
        #If this is a new user
        if ((not this.store.exists('secretKey')) or (this.store.get("secretKey")["value"] == '')):
            #First initiates everything within the json file
            this.store.put("numEntries", value = 0)
            this.store.put("macDict", value = dict())
            this.store.put("recentTen", value = list())
            this.store.put("prevNetwork", value = dict())
            this.store.put("homeLabel", value = "Status: Account Registered")
            this.store.put("quitAppLabel", value = "Status: Click to delete all data")
            this.store.put("sendDataLabel", value = "Status: Click to report infected")
            this.store.put("homeLabelColor", value = [1, 1, 1, 1])
            this.store.put("quitAppLabelColor", value = [1, 1, 1, 1])
            this.store.put("sendDataLabelColor", value = [1, 1, 1, 1])
            this.store.put("isInfected", value = False)
            #Sets the secretCode to be empty screen
            Logger.info('Secret Key set to ' + 'empty string')
            this.store.put("secretKey", value = '')
            Logger.info('Self Mac Address set to ' + self.macClass.getMacSelf()[0])
            #Stores the personal mac address in the JSON file
            this.store.put("selfMac", value = self.macClass.getMacSelf()[0])
            #First checks for internet
            if (not isInternet()):
                this.store.put("homeLabel", value = "Status: Unable to connect to internet. Please check internet connection")
                isSuccessful = False
            #Stores the returned secret key in tempSecret if internet found
            else:
                tempSecret = client.initSelf(this.store.get("selfMac")["value"])
                if type(tempSecret) == str:
                    if (len(tempSecret) == 56):
                        #All initialization
                        Logger.info('Secret Key set to ' + tempSecret)
                        this.store.put("secretKey", value = tempSecret)
                elif (tempSecret == 2):
                    this.store.put("homeLabel", value = "Status: Server Error, Please quit the app and try again (2)")
                    isSuccessful = False
                elif (tempSecret == 3):
                    this.store.put("homeLabel", value = "Status: User already initiated. Please quit the app and try again (3)")
                    isSuccessful = False
                elif (tempSecret == 4):
                    this.store.put("homeLabel", value = "Status: Invalid Mac Address, Please quit the app and try again (4)")
                    isSuccessful = False
                else:
                    this.store.put("homeLabel", value = "Status: Unknown error occurred. Please restart the app. If this persists, please contact developers. ")
                    isSuccessful = False
        #If initialization or permanant storage found and successful
        if (isSuccessful):
            #Stores self mac address in selfMacAddress class variable
            self.selfMacAddress = self.store.get("selfMac")["value"]
            #Stores the actual mac addresses that we get from getMac into class instance variable actualMac
            #This is used to display the network mac addresses the first time users ppen the app
            self.actualMac = "\nMAC On Current Network : \n\n" + self.macClass.getMac()
            cutoff = datetime.datetime.now() - datetime.timedelta(days=14)
            macDict = this.store.get("macDict")["value"]
            pauseThread(this.myClockThread)
            newMacDict = {}
            for mac in macDict.keys():
                strTime = macDict[mac]
                dateSeen = datetime.datetime.strptime(strTime, '%Y-%m-%d_%H:%M:%S')
                if not dateSeen < cutoff:
                    newMacDict[mac] = macDict[mac]
            this.store.put("macDict", value = newMacDict)
            del macDict
            del newMacDict
            resumeThread(this.myClockThread)
        #This should at least guarantee the gui to run but set everything to empty.
        else:
            this.store.put("homeLabelColor", value = [1, 0, 0, 1])
            self.selfMacAddress = ""
            self.actualMac = "\nMAC On Current Network : \n\n" + ""
            showError()
        #The line of code that calls the function runTimeFunction every 20 ticks


    #This method is used when we click the button to check our current network mac and confirm with the server
    def calculateMac(self):
        #actualMac is the variable that stores the current network after arp-a again
        self.actualMac = "\nMAC On Current Network : \n\n" + self.macClass.getMac()
        #This line checks with the server to see if user has already contacted infected individual
        self.coronaCatcherButtonClicked()
        Logger.info('Calculated MAC Addr to be ' + self.actualMac)
        Logger.info(self.macClass.getString(self.store.get("prevNetwork")["value"]))
        #This changes the displayed text into the current network by formatting it with the getString method in the macClass
        self.macDisplay.text = self.macClass.getString(self.store.get("prevNetwork")["value"])
        return self.actualMac


    #This function sends selfMacAddress to the server and stores the reply in the statusLabel variable in JSON
    def coronaCatcherButtonClicked(self):
        Logger.info('coronaCatcherButtonClicked ')
        if "LastQueryTime" in this.store:
            lastAccess = this.store.get("LastQueryTime")['value']
            lastAccess = datetime.datetime.strptime(lastAccess, '%Y-%m-%d_%H:%M:%S.%f')
        else:
            lastAccess = datetime.datetime.fromisoformat('2011-11-04 00:05:23.283')
        allowedTime = lastAccess + datetime.timedelta(hours=8)
        currentTime = datetime.datetime.now()
        if allowedTime < currentTime:
            if (not isInternet()):
                showErrorInternet()
            else:
                returnVal = client.queryMyMacAddr(this.store.get("selfMac")["value"], this.store.get("secretKey")["value"])
                now = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
                if (returnVal == -1):
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou have contacted someone allegedly with the virus. Please quarantine"
                    this.store.put("homeLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou have contacted someone with the virus. Please quarantine")
                    this.store.put("LastQueryTime", value = now)
                    this.store.put("homeLabelColor", value = [1, 0, 0, 1])
                    self.statusLabel.background_color = (1, 0, 0, 1)
                elif (returnVal == -2):
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou have contacted someone confirmed with the virus. Please quarantine"
                    this.store.put("homeLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou have contacted someone with the virus. Please quarantine")
                    this.store.put("LastQueryTime", value = now)
                    this.store.put("homeLabelColor", value = [1, 0, 0, 1])
                    self.statusLabel.background_color = (1, 0, 0, 1)
                elif (returnVal == 0):
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou are still safe!"
                    this.store.put("homeLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nyou are still safe!")
                    this.store.put("homeLabelColor", value = [0, 1, 0, 1])
                    this.store.put("LastQueryTime", value = now)
                    self.statusLabel.background_color = (0, 1, 0, 1)
                elif (returnVal == 2):
                    showErrorServer()
                elif (returnVal == 3):
                    showErrorSecret()
                elif (returnVal == 4):
                    showErrorMAC()
                elif (returnVal == 5):
                    showErrorTime()
                else:
                    showErrorCatchAll()
        #Requested to server within 8 hour timeframe
        else:
            showErrorActualTime(allowedTime)

    


#SideBar class page (reference my.kv file)
class SideBarPage(Screen):
    pass

#AboutUs class page (reference my.kv file)
class AboutUsPage(Screen):
    #Method that returns the about us text including email (sorry we don't want scam emails)
    def getEm(self):
        a = "lively"
        b = 87
        c = "carpet"
        d = "@gm"
        e = "ail.com"
        firstMail = a + c + str(b) + d +e
        f = "rya"
        g = "nyxw"
        h = 200
        i = "2@gm"
        j = "ail.c"
        k = "om"
        secondMail = f + g + str(h) + i + j + k
        first = "Thank you for using our app. We are a group of students based in Shanghai, China. Through this app, we hope to do our part to ending this devastating pandemic. \n\nTo contact us, or if there are any issues, please reach us in the following email address : \n"
        return first + firstMail + "\n" + secondMail
    pass

#QuitApp class page (reference my.kv file)
class QuitAppPage(Screen):
    def __init__(self, **kwargs):
        Logger.info('creating an instance of QuitAppPage')
        self.store = this.store
        super(QuitAppPage, self).__init__(**kwargs)
        self.quitCount = 0
        self.statusLabel = ObjectProperty(None)
    
    #This method runs when the deleteDataAndQuit button is clicked
    def deleteDataAndQuitButtonClicked(self):
        pauseThread(this.myClockThread)
        Logger.info('Delete data and quit clicked')
        self.quitCount += 1
        self.getCount()
        if (self.quitCount % 5 == 0):
            self.clearCounter()
            if (not isInternet()):
                showErrorInternet()
            else:
                returnValue = client.forgetUser(this.store.get("selfMac")["value"], this.store.get("secretKey")["value"])
                if (returnValue == 0):
                    this.deleteAllData = True
                    Logger.info('Marked local files for deletion')
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nSucess! You may quit the app"
                    this.store.put("quitAppLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nSucess! You may quit the app")
                    this.store.put("quitAppLabelColor", value = [0, 1, 0, 1])
                    self.statusLabel.background_color = (0, 1, 0, 1)
                elif (returnValue == 2):
                    showErrorServer()
                    
                elif (returnValue == 3):
                    
                    
                    showErrorSecret()
                elif (returnValue == 4):
                    showErrorMAC()
                elif (returnValue == 1):
                    showErrorCatchAll()
                else:
                    showErrorCatchAll()
    def resumeThread(self):
        resumeThread(this.myClockThread)
    def getCount(self):
        origText = self.statusLabel.text
        if (origText[-1].isnumeric()):
            self.statusLabel.text = origText[:-9] + " |  Del:" + str(6 - self.quitCount%6)
        else:
            self.statusLabel.text = origText + " |  Del:" + str(6 - self.quitCount%6)
    #Clears the counter when the user hits "back"
    def clearCounter(self):
        self.quitCount = 0;
        self.getCount()
        
        
#SendData class page (reference my.kv file)
class SendDataPage(Screen):
    def __init__(self, **kwargs):
        super(SendDataPage, self).__init__(**kwargs)
        self.store = this.store
        #Used to store number of clicks
        self.infectedCount = 0
        self.recoveredCount = 0
        Logger.info('creating an instance of SendDataPage')
        self.statusLabel = ObjectProperty(None)
    #This method is called when the ImInfected button is clicked
    def imInfectedButtonClicked(self):
        Logger.info('imInfected button clicked')
        self.infectedCount += 1
        self.recoveredCount = 0
        if (self.infectedCount % 6 == 0):
            self.clearCounter()
            if (not isInternet()):
                showErrorInternet()
            else:
                returnVal = client.positiveReport(this.store.get("selfMac")["value"], this.store.get("secretKey")["value"], self.getCSVString())
                if (returnVal == 2):
                    showErrorServer()
                elif (returnVal == 3):
                    showErrorSecret()
                elif (returnVal == 4):
                    showErrorCSV()
                else:
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nRequest sucess! Get well soon!"
                    this.store.put("sendDataLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nRequest sucess! Get well soon!")
                    this.store.put("sendDataLabelColor", value = [0, 1, 0, 1])
                    self.statusLabel.background_color = (0, 1, 0, 1)
                    this.store.put("isInfected", value = True)
        else:
            self.getCount()
    #Clears the counter when user hits "back"
    def clearCounter(self):
        self.infectedCount = 0
        self.recoveredCount = 0
        self.getCount()
    #Convers a dictionary to a string used for permanent storage and sending to server
    def getCSVString(self):
        returnStr = this.store.get("selfMac")["value"] + ","
        macDictionary = this.store.get("macDict")["value"]
        for key in macDictionary:
            returnStr += key + ","
        return returnStr
    
    
    
    def getCount(self):
        origText = self.statusLabel.text
        if (origText[-1].isnumeric()):
            self.statusLabel.text = origText[:-15] + " |  Inf:" + str(6 - self.infectedCount%6) + " Rec:" + str(6 - self.recoveredCount%6)
        else:
            self.statusLabel.text = origText + " |  Inf:" + str(6 - self.infectedCount%6) + " Rec:" + str(6 - self.recoveredCount%6)


    #This method is called when the iJustRecovered button is clicked
    def iJustRecoveredButtonClicked(self):
        Logger.info('iJustRecovered button clicked')
        self.recoveredCount += 1
        self.infectedCount = 0
        if (self.recoveredCount % 6 == 0):
            self.clearCounter()
            if (not this.store.get("isInfected")["value"]):
                showErrorLogic()
            elif (not isInternet()):
                showErrorInternet()
            else:
                returnVal = client.negativeReport(this.store.get("selfMac")["value"], this.store.get("secretKey")["value"])
                if (returnVal == 2):
                    showErrorServer()
                elif (returnVal == 3):
                    showErrorSecret()
                elif (returnVal == 4):
                    showErrorMAC()
                else:
                    self.statusLabel.text = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nRequest sucess! Good job recovering! "
                    this.store.put("sendDataLabel", value = "Checked by " + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + ", \nRequest sucess! Good job recovering! ")
                    this.store.put("sendDataLabelColor", value = [0, 1, 0, 1])
                    self.statusLabel.background_color = (0, 1, 0, 1)
                    this.store.put("isInfected", value = False)
        else:
            self.getCount()
#SeeDataPage class page (reference my.kv file)
class SeeDataPage(Screen):
    def __init__(self, **kwargs):
        super(SeeDataPage, self).__init__(**kwargs)
        Logger.info('creating an instance of SeeDataPage')
        self.store = this.store
        #Stores the recentTen aspect of the json file, used for the first initiation of the user
        self.recentTen = this.store.get("recentTen")["value"]
        #This variable references the label within the page (used for potentially changing the top10 by renewing)
        self.displayTen = ObjectProperty(None)
        Logger.info("BEFORE ASSIGN VALUES")

    #This method changes the self.data so that it reflects the new recentTen
    def renewRecentTen(self):
        Logger.info('Renew Recent Ten button clicked')
        self.recentTen = this.store.get("recentTen")["value"]
        self.displayTen.text = self.convertRecentTenToStr()

    #This method converts the recentTen class variable to a string
    def convertRecentTenToStr(self):
        returnStr = ""
        for pair in self.recentTen:
            returnStr += "Time: " + pair[0] + " - Mac: " + pair[1] + "\n\n\n"
        return returnStr

#Represent the transitions between the windows above
class WindowManager(ScreenManager):
    pass



def killThread(clockThread): # permanantly kill the thread (call on exit)
    Logger.info("Sending SIGKILL to thread")
    clockThread.enabled = False

def pauseThread(clockThread): # Pauses the thread if it is not scanning for Mac Address
    Logger.info("Sending Pause to thread")
    clockThread.running = False

def resumeThread(clockThread):
    Logger.info("Sending Resume to thread")
    clockThread.running = True

#Kivy file used for formatting
kivyFile = '''
WindowManager:
    HomePage:
    SideBarPage:
    AboutUsPage:
    QuitAppPage:
    SendDataPage:
    SeeDataPage:
<BackgroundColor@Widget>
    background_color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: root.background_color
        Rectangle:
            size: self.size
            pos: self.pos
<ScaleLabel@Label+BackgroundColor>:
	background_color: 0, 0, 0, 0
    _scale: 1. if self.texture_size[0] < self.width else float(self.width) / self.texture_size[0]
	canvas.before:
		PushMatrix
		Scale:
			origin: self.center
			x: self._scale or 1.
			y: self._scale or 1.
	canvas.after:
		PopMatrix

<-ScaleButton@Button+BackgroundColor>:
    background_color: 0, 0, 0, 0
	state_image: self.background_normal if self.state == 'normal' else self.background_down
	disabled_image: self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
	_scale: 1. if self.texture_size[0] < self.width else float(self.width) / self.texture_size[0]
	canvas:
		Color:
			rgba: self.background_color
		BorderImage:
			border: self.border
			pos: self.pos
			size: self.size
			source: self.disabled_image if self.disabled else self.state_image
		PushMatrix
		Scale:
			origin: self.center
			x: self._scale or 1.
			y: self._scale or 1.
		Color:
			rgba: self.disabled_color if self.disabled else self.color
		Rectangle:
			texture: self.texture
			size: self.texture_size
			pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)
		PopMatrix




<ErrorPopupServer>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Server Error / Server out of memory"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "Please quit the app and retry (2)"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopup>:
    ScaleButton:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleButton:
        text: "User Initiation Not Successful"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleButton:
        text: "Please quit the app and try again"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopupSecret>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Incorrect secret key"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "Please quit the app and retry (3)"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}


<ErrorPopupTime>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Please only check once every 8 hours."
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "This is a precaution to not overload our servers"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopupCSV>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Invalid CSV, please restart your APP and try again"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "If problem persists, please contact developers"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopupInternet>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "No Internet Connection"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}

    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}


<ErrorPopupMAC>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Invalid MAC address"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "Please quit the app and try again (4)"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopupActualTime>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Please only check once every 8 hours."
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "Look above to see your next opportunity to check"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}

<ErrorPopupCatchAll>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "Unknown error occurred. Please restart the app"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}
    ScaleLabel:
        text: "If this persists, please contact developers"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.2}
    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}


<ErrorPopupLogic>:
    ScaleLabel:
        size_hint: 0.6, 0.2
        text: "An Error has Occured! "
        pos_hint: {"x": 0.2, "top": 1}
    ScaleLabel:
        text: "You must first get infected to recover"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0.4}

    ScaleLabel:
        text: "Click anywhere outside error box to continue"
        size_hint: 0.8, 0.2
        pos_hint: {"x": 0.1, "y": 0}


<SeeDataPage>:
    name: "seedata"
    displayTen: display
    ScaleLabel:
        pos_hint: {"center_x": 0.5, "center_y": 0.86}
        size_hint: 0.7, 0.04
        text: "Recent Added Mac Addresses"
        background_color: 1, 0, 0, 0.5
    ScaleButton:
        id: display
        pos_hint: {"center_x": 0.5, "center_y": 0.4375}
        size_hint: 0.7, 0.7
        text: root.convertRecentTenToStr()
        text_size: self.size
        halign: "center"
        valign: "top"
    ScaleButton:
        pos_hint: {"x": 0.05, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Options"
        on_release:
            app.root.current = "sidebar"
            root.manager.transition.direction = "right"

    ScaleButton:
        pos_hint: {"right": 0.95, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Renew"
        on_release:
            root.renewRecentTen()


<SideBarPage>:
    name: "sidebar"
    GridLayout:
        cols: 1


        ScaleButton:
            text: "Home"
            background_color: 1, 1, 1, 1
            on_release:
                app.root.current = "home"
                root.manager.transition.direction = "right"

        ScaleButton:
            text: "About Us / Contact Us"
            background_color: 1, 1, 1, 0.8
            on_release:
                app.root.current = "aboutus"
                root.manager.transition.direction = "left"

        ScaleButton:
            text: "My MAC Addresses"
            background_color: 1, 1, 1, 0.6
            on_release:
                app.root.current = "seedata"
                root.manager.transition.direction = "left"

        ScaleButton:
            text: "Delete Data & Quit"
            background_color: 1, 1, 1, 0.4
            on_release:
                app.root.current = "quitapp"
                root.manager.transition.direction = "left"

        ScaleButton:
            text: "I'm Infected"
            background_color: 1, 1, 1, 0.2
            on_release:
                app.root.current = "senddata"
                root.manager.transition.direction = "left"

<SendDataPage>:
    name: "senddata"
    statusLabel : status
    ScaleButton:
        pos_hint: {"x": 0.05, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Options"
        on_release:
            root.clearCounter()
            app.root.current = "sidebar"
            root.manager.transition.direction = "right"
    ScaleButton:
        pos_hint: {"center_x": 0.5, "center_y": 0.7}
        background_color: 1, 0, 0, 1
        size_hint: 0.7, 0.12
        text: "I Tested Positive (Click 6 times)"
        on_release:
            root.imInfectedButtonClicked()
    ScaleButton:
        pos_hint: {"center_x": 0.5, "center_y": 0.55}
        background_color: 0, 1, 0, 1
        size_hint: 0.7, 0.12
        text: "I Recovered (Click 6 times)"
        on_release:
            root.iJustRecoveredButtonClicked()
    ScaleButton:
        id: status
        background_color: root.store.get("sendDataLabelColor")["value"][0], root.store.get("sendDataLabelColor")["value"][1], root.store.get("sendDataLabelColor")["value"][2], root.store.get("sendDataLabelColor")["value"][3]
        pos_hint: {"center_x": 0.5, "bottom": 0}
        text: root.store.get("sendDataLabel")["value"]
        size_hint: 1, 0.1

<AboutUsPage>:
    name: "aboutus"

    ScaleButton:
        pos_hint: {"x": 0.05, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Options"
        on_release:
            app.root.current = "sidebar"
            root.manager.transition.direction = "right"
    ScaleLabel:
        pos_hint: {"center_x": 0.5, "center_y": 0.8}
        size_hint: 0.7, 0.1
        text: "Our Team"
    Label:
        pos_hint: {"center_x": 0.5, "center_y": 0.375}
        size_hint: 0.7, 0.6
        text_size: self.size
        halign: "center"
        valign: "top"
        text: root.getEm()

<HomePage>:
    name: "home"
    statusLabel : status
    macDisplay: mac
    background_color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: root.background_color
        Rectangle:
            size: self.size
            pos: self.pos
    ScaleButton:
        pos_hint: {"x": 0.05, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Options"
        on_release:
            app.root.current = "sidebar"
            root.manager.transition.direction = "left"
    ScaleButton:
        pos_hint: {"center_x":0.5, "center_y": 0.8 }
        background_color: 1, 0, 0, 1
        size_hint: 0.7, 0.2
        text: "Click To Check My Risk (Once every 8 hours)"
        on_release:
            root.calculateMac()
        halign: "center"
        valign: "middle"
    ScaleLabel:
        id: mac
        pos_hint: {"center_x": 0.5, "center_y": 0.45}
        background_color: 0, 0, 0, 1
        size_hint: 0.7, 0.4
        text: root.actualMac
        text_size: self.size
        halign: "center"
        valign: "top"
    ScaleButton:
        pos_hint: {"center_x": 0.5, "center_y": 0.175}
        size_hint: 0.7, 0.05
        background_color: 0, 0, 0, 1
        text: "Your Mac: " + root.selfMacAddress
    ScaleButton:
        id: status
        background_color: root.store.get("homeLabelColor")["value"][0], root.store.get("homeLabelColor")["value"][1], root.store.get("homeLabelColor")["value"][2], root.store.get("homeLabelColor")["value"][3]
        pos_hint: {"center_x": 0.5, "bottom": 0}
        text: root.store.get("homeLabel")["value"]
        size_hint: 1, 0.1
        
<QuitAppPage>:
    name: "quitapp"
    statusLabel : status
    ScaleButton:
        pos_hint: {"x": 0.05, "top": 0.97}
        background_color: 1, 1, 1, 1
        size_hint: 0.2, 0.05
        text: "Options"
        on_release:
            root.resumeThread()
            root.clearCounter()
            app.root.current = "sidebar"
            root.manager.transition.direction = "right"
    ScaleButton:
        pos_hint: {"center_x": 0.5, "center_y": 0.7}
        background_color: 1, 0, 0, 1
        size_hint: 0.7, 0.12
        text: "Delete Data (Click 6 times)"
        on_release:
            root.deleteDataAndQuitButtonClicked()
    ScaleButton:
        id: status
        background_color: root.store.get("quitAppLabelColor")["value"][0], root.store.get("quitAppLabelColor")["value"][1], root.store.get("quitAppLabelColor")["value"][2], root.store.get("quitAppLabelColor")["value"][3]
        pos_hint: {"center_x": 0.5, "bottom": 0}
        text: root.store.get("quitAppLabel")["value"]
        size_hint: 1, 0.1




'''

#Loads the above kivy string into the builder
kv = Builder.load_string(kivyFile)

#Class that builds the entire app
class MyMainApp(App):
    def build(self):
        return kv


#Runs the app
if __name__ == "__main__":
    try:
        Logger.info('App Started')
        MyMainApp().run()
        Logger.info('App Exiting')
        killThread(this.myClockThread)
        client.freeResources()
        f = open(this.appPath + os.sep + "main.log", "a")
        for log in LoggerHistory.history:
            f.write(repr(log) +'\n')
        f.close()
        if this.deleteAllData:
            for entry in os.scandir(this.appPath):
                if (not entry.path.endswith(".py") and not entry.path.endswith(".kv")) and entry.is_file():
                    os.remove(entry.path)
            Logger.info('Deleted local storage')
        exit()
    except KeyboardInterrupt:
        Logger.critical('App Exiting')
        killThread(this.myClockThread)
        f = open(this.appPath + os.sep + "main.log", "a")
        for log in LoggerHistory.history:
            f.write(repr(log) +'\n')
        f.close()
        client.freeResources()
        if this.deleteAllData:
            for entry in os.scandir(this.appPath):
                if (not entry.path.endswith(".py") and not entry.path.endswith(".kv")) and entry.is_file():
                    os.remove(entry.path)
            Logger.info('Deleted local storage')
        exit()
    except Exception as e:
        Logger.critical("Exception occurred", exc_info=True)
