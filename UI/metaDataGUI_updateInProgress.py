# from main_utility import *
#%%
import numpy as np
import sys, os, json, traceback
from glob import glob
from pathlib import Path
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QListWidget, 
    QCheckBox, 
    QPushButton, 
    QComboBox,  
    QHBoxLayout, 
    QLabel, 
    QErrorMessage, 
    QApplication, 
    QMainWindow, 
    QTextEdit, 
    QVBoxLayout, 
    QWidget, 
    QGroupBox
)
from PyQt6.QtCore import (
    Qt, 
    pyqtSignal, 
    QThreadPool
)
from PyQt6.QtGui import (
    QImage, 
    QPixmap, 
    QColor
)
from datetime import datetime, date
import fitz #PyMuPDF
from main_utility import *
from metaDataWorker import WorkerSignals, metaDataWorker, transferToScratchWorker, cloudTransferWorker

today = str(date.today())
print('Running Data Viewer on:', today)
dataDir = 'Y:/' #setting to scratch save location

#Creating a seperate class that can help user verify what boxes are valid by just clicking on them
class userValidatableTextEdit(QTextEdit):
    tab = pyqtSignal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_color = QColor('white')
        self.clicked_color = QColor('lightblue')
        self.isGreen = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isGreen:
                self.setStyleSheet(f'background-color: {self.default_color.name()}')
            else:
                self.setStyleSheet(f'background-color: {self.clicked_color.name()}')
        super().mousePressEvent(event)
    def setDefaultColor(self):
        self.setStyleSheet(f'background-color: {self.default_color.name()}')
        self.isGreen = False
    def resetColor(self):
        if not self.isGreen:
            self.setStyleSheet(f'background-color: {self.default_color.name()}')
    def setColorToGreen(self):
        self.setStyleSheet('background-color: green')
        self.isGreen=True
    def keyPressEvent(self,event):
        if event.key() == 16777217:
            event.accept()
            self.tab.emit(event)
        else:
            super().keyPressEvent(event)
        
class processingMouseWindow(QWidget):
    def __init__(self, threadingPool, localWorkerParams):
        super().__init__()
        self.setWindowTitle("Secondary Window")
        self.setGeometry(100, 100, 300, 200)
        self.threadingPool = threadingPool
        self.params = localWorkerParams
        closeWindow = pyqtSignal(object)
        '''
        TODO:
        Design Layout to show mouse wr name at tope
        2 gifs representing data transfer and mouse data processing
        button at the bottom that becomes active if processing is done or if error occurs
        '''
        self.layout = QVBoxLayout()
        self.mouseWorking = QLabel(f'Processing {str(self.params['WRname'])}')
        self.layout.addWidget(self.mouseWorking)
        
        #put gifs here
        self.gifLayout = QHBoxLayout()
        #self.gifLayout.addWidget(self.fileTransferGif)
        #self.gifLayout.addWidget(self.processBehaviorGif)
        self.layout.addLayout(self.gifLayout)
        
        
        self.setLayout(self.layout)

        self.transferAndProcess()
    def transferAndProcess(self):
        #set up signals
        signals = WorkerSignals()
        signals.nextStep.connect(self.onNextStep)
        signals.stepComplete.connect(self.onStepComplete)
        signals.allComplete.connect(self.onFullCompletion)
        signals.transmitData.connect(self.onDataTransmission)
        signals.error.connect(self.onError)
        self.threadingPool.start(transferToScratchWorker(signals, self.paramDict))


    def closeEvent(self,event):
        self.closeWindow.emit(self)
        super().closeEvent(event)


class BergamoDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Viewer')

        #Define Init Variables
        self.paramDict = {}
        self.miceAvailable = glob('Y:/*') 
        self.listOfMice = os.listdir('Y:/')
        self.selectedPaths=None
        self.datesToLook= []
        self.datesDropDownActive = False
        self.selectedMouse = None
        self.pageSelect = 3
        self.dataPathEntry = None
        self.localDataStorage = None
        self.threadingPool = QThreadPool.globalInstance()
        self.runningWorkers = []
        self.initUI()

    def initUI(self):
        
        #fixed height for entry boxes
        h = 65
        
        #Setting Central Widget
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        
        #defining the background layout everything will be put in vertically
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)
        
        #######################################################
        ############## App Heading Stuff ######################
        #######################################################
        
        
        #Exit button at top of window, makes it easier to close everything appropriately
        exit_button = QPushButton('Exit')
        exit_button.clicked.connect(self.close)
        mainLayout.addWidget(exit_button)
        
        #Defining the Mouse Drop Down in a more readable way
        self.mouseNameDropDown =  QComboBox(self)
        mice = []
        for file in self.miceAvailable:
            if os.path.isdir(file):
                mouseWRname = file.split('/')[-1]
                if mouseWRname.count('_')>1:
                    mice.append('_'.join(mouseWRname.split('_')[:-1]))
                else:
                    mice.append(mouseWRname.split('_')[0])
        uniqueMice = np.unique(mice)
        for mouse in uniqueMice:
            self.mouseNameDropDown.addItem(f'{mouse}')
        self.mouseNameDropDown.setCurrentIndex(0) #does not run function because not linked yet
        self.mouseNameDropDown.currentIndexChanged.connect(self.selectionChanged)

        #######################################################
        ############## Entry Info Here ########################
        #######################################################
        
        #If Entering a new mouse, just enter ID here first 
        self.mouseEntryLabel = QGroupBox('Mouse Info') #goes left top
        self.mouseEntryLabel.setFixedSize(800,350)

        self.processingStatusListLabel = QGroupBox('Processing Mice') #goes right top
        self.processingStatusListLabel.setFixedSize(200,350)
        
        self.processingLayout = QVBoxLayout()
        self.processingStatusList = QListWidget(self)
        self.processingLayout.addWidget(self.processingStatusList) # going inside processingStatusListLabel
        self.processingStatusListLabel.setLayout(self.processingLayout)

        #mouse entry AND processing status both fit inside mouseEntry label
        self.mouseEntryLayout = QHBoxLayout()

        self.mainMouseEntryLayout = QVBoxLayout()
        self.mouseEntryLayout_layer1 = QHBoxLayout()
        self.mouseEntryLayout_layer2 = QHBoxLayout()
        self.mouseEntryLayout_layer3 = QHBoxLayout()
        self.mouseEntryLayout_layer4 = QHBoxLayout()
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer1)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer2)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer3)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer4)
        self.mouseEntryLabel.setLayout(self.mainMouseEntryLayout) #setting label box to be v

        # Left label is entry area, right label is list
        self.mouseEntryLayout.addWidget(self.mouseEntryLabel) 
        self.mouseEntryLayout.addWidget(self.processingStatusListLabel)        

        #Layer 1
        self.WRName = userValidatableTextEdit()                 #Define Edit
        self.WRName.tab.connect(self.tabToSwitch)               #Define tab event
        self.WRNameLabel = QGroupBox('Mouse WR Name')           #Define Label
        self.WRNameLabel.setFixedHeight(h)                      #Set Height
        self.WRNameLayout = QVBoxLayout()                       #Define Layout
        self.WRNameLayout.addWidget(self.WRName)                #Edit into Layout
        self.WRNameLabel.setLayout(self.WRNameLayout)           #Layout into Box
        self.mouseEntryLayout_layer1.addWidget(self.WRNameLabel)#Box into layer of layout
        
        self.mouseID = userValidatableTextEdit() 
        self.mouseIDLabel = QGroupBox('Mouse ID')
        self.mouseIDLabel.setFixedHeight(h)
        self.mouseIDLayout = QVBoxLayout()
        self.mouseIDLayout.addWidget(self.mouseID)
        self.mouseIDLabel.setLayout(self.mouseIDLayout)
        self.mouseEntryLayout_layer1.addWidget(self.mouseIDLabel)
        
        #Layer 2
        self.imageWaveLength = userValidatableTextEdit() 
        self.imageWaveLengthLabel = QGroupBox('Imaging Wavelength')
        self.imageWaveLengthLabel.setFixedHeight(h)
        self.imageWaveLengthLayout = QVBoxLayout()
        self.imageWaveLengthLayout.addWidget(self.imageWaveLength)
        self.imageWaveLengthLabel.setLayout(self.imageWaveLengthLayout)
        self.mouseEntryLayout_layer2.addWidget(self.imageWaveLengthLabel)
        
        self.imagingDepth = userValidatableTextEdit()
        self.imagingDepthLabel = QGroupBox('Imaging Depth')
        self.imagingDepthLabel.setFixedHeight(h)
        self.imagingDepthLayout = QVBoxLayout()
        self.imagingDepthLayout.addWidget(self.imagingDepth)
        self.imagingDepthLabel.setLayout(self.imagingDepthLayout)
        self.mouseEntryLayout_layer2.addWidget(self.imagingDepthLabel)
        
        self.experimenterName = userValidatableTextEdit()
        self.experimenterNameLabel = QGroupBox('Experimenter Name')
        self.experimenterNameLabel.setFixedHeight(h)
        self.experimenterNameLayout = QVBoxLayout()
        self.experimenterNameLayout.addWidget(self.experimenterName)
        self.experimenterNameLabel.setLayout(self.experimenterNameLayout)
        self.mouseEntryLayout_layer2.addWidget(self.experimenterNameLabel)
        
        self.sessionDate = userValidatableTextEdit()
        self.sessionDate.setPlainText(today)
        self.sessionDateLabel = QGroupBox('Date of Session')
        self.sessionDateLabel.setFixedHeight(h)
        self.sessionDateLayout = QVBoxLayout()
        self.sessionDateLayout.addWidget(self.sessionDate)
        self.sessionDateLabel.setLayout(self.sessionDateLayout)
        self.mouseEntryLayout_layer2.addWidget(self.sessionDateLabel)
        
        self.targetStruct = userValidatableTextEdit()
        self.targetStruct.setPlainText('Primary Motor Cortex')
        self.targetStructLabel = QGroupBox('Targeted Brain Structure')
        self.targetStructLabel.setFixedHeight(h)
        self.targetStructLayout = QVBoxLayout()
        self.targetStructLayout.addWidget(self.targetStruct)
        self.targetStructLabel.setLayout(self.targetStructLayout)
        self.mouseEntryLayout_layer3.addWidget(self.targetStructLabel)
    
        #Layer 4
        self.notes = userValidatableTextEdit()
        self.notesLabel = QGroupBox('Session Notes')
        self.notesLabel.setFixedHeight(75)
        self.notesLayout = QVBoxLayout()
        self.notesLayout.addWidget(self.notes)
        self.notesLabel.setLayout(self.notesLayout)
        self.mouseEntryLayout_layer4.addWidget(self.notesLabel)

        # TODO: COMBINE BUTTONS
        #putting a "transfer local data to scratch" button here
        self.processMouseButton = QPushButton('Process Mouse')
        self.mainMouseEntryLayout.addWidget(self.processMouseButton)
        self.processMouseButton.clicked.connect(self.processMouse)#(self.copyToScratch)
        
        
        #Process Data Button goes after data is entered
        # self.processDataButton = QPushButton('Process Data')
        # self.mainMouseEntryLayout.addWidget(self.processDataButton)
        # # self.processDataButton.clicked.connect(self.initiatePipeline)
        
        #######################################################
        ##############  Display Plots #########################
        #######################################################

        self.plotVisualizationLayout = QVBoxLayout()
        self.plotVisualizationLabel = QGroupBox('Visualizing Plots')
        self.pageSelectionUI = QHBoxLayout()
        
        #First Select Date
        self.mouseDateDropdown = QComboBox(self)
        self.mouseDateDropdown.addItem('-')
        self.mouseDateDropdown.setEnabled(self.datesDropDownActive)
        self.mouseDateDropdown.currentIndexChanged.connect(self.loadPDF)
        
        #PDF Page Selection
        self.leftButton = QPushButton('<')
        self.leftButton.clicked.connect(self.leftPageFunc)
        self.rightButton = QPushButton('>')
        self.rightButton.clicked.connect(self.rightPageFunc)
        self.pageSelectionUI.addWidget(self.leftButton)
        self.pageSelectionUI.addWidget(self.rightButton)
        
        #PDF Visualization
        self.pdfLoc = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        
        #Make YAML Button
        self.sendToCloudButton = QPushButton('Send Info To Cloud')
        self.sendToCloudButton.clicked.connect(self.sendToCloud)
        
        #Organizing visualization section
        self.plotVisualizationLabel.setLayout(self.plotVisualizationLayout)
        self.plotVisualizationLayout.addWidget(self.mouseDateDropdown) #date selection layer
        self.plotVisualizationLayout.addLayout(self.pageSelectionUI)   #page selection layer
        self.plotVisualizationLayout.addWidget(self.sendToCloudButton)
        self.plotVisualizationLayout.addWidget(self.pdfLoc)


        #######################################################
        ##############  Organize Layout #######################
        #######################################################
        
        #Define the order things are placed
        #Main Layout --> QVBoxLayout
        mainLayout.addWidget(exit_button)
        mainLayout.addWidget(self.mouseNameDropDown)
        mainLayout.addLayout(self.mouseEntryLayout)
        mainLayout.addWidget(self.plotVisualizationLabel)

        self.show()
    
        #######################################################
        ##############  FUN-ctions ############################
        #######################################################

    def tabToSwitch(self, event):
        thisMouse = self.WRName.toPlainText()
        if event.key():
            if thisMouse in self.listOfMice:
                with open('Y:/mouseDict.json', 'r') as f:
                    mouseDict = json.load(f)
                if thisMouse in mouseDict.keys():
                    whereMouseIs = [ i for i in range(self.mouseNameDropDown.count()) if self.mouseNameDropDown.itemText(i) == thisMouse]
                    self.mouseNameDropDown.setCurrentIndex(whereMouseIs[0])
                    mouseDates = []
                    for j in range(self.mouseDateDropdown.count()):
                        try:
                            mouseDates.append(datetime.strptime(self.mouseDateDropdown.itemText(j), '%m%d%y'))
                        except Exception:
                            pass 
                    sortedDates = [date.strftime('%m%d%y') for date in sorted(mouseDates)]
                    for date in sortedDates:
                        if os.path.exists(f'Y:/{thisMouse}/{date}/session.json'):
                            mostRecentDate = date
                    mostRecentIDX = [dateIDX for dateIDX in range(self.mouseDateDropdown.count()) if self.mouseDateDropdown.itemText(dateIDX) == mostRecentDate]
                    self.mouseDateDropdown.setCurrentIndex(mostRecentIDX[0])
            else:
                print('Mouse not specified!')


    def resetTextEditColor(self, event):
        widget = self.sender()
        if isinstance(widget, userValidatableTextEdit):
            widget.set_default_color()
        super(QTextEdit, self).focusOutEvent(event)

    def matchIDFunc(self):
        mouseDictPath = dataDir+'/mouseDict.json'
        with open(mouseDictPath, 'r') as f:
            mouseDict = json.load(f)
        if self.WRName.toPlainText() in mouseDict.keys():
            mouseID = mouseDict[self.wrName.toPlainText()]
            self.mouseID.setPlainText(str(mouseID))
        else:
            err = QErrorMessage(self)
            err.showMessage('This is a new mouse! Enter ID and Process First Data')
            err.exec()
    
    def processMouse(self):
        # TODO: 
        #   -   also pass boolean array the tells what specific processing you want done (based off check boxes)
        #   -   ADD ALL OPEN WINDOWS TO A QLIST
        processingArray = [1, 1, 1]                                                             #temporarily will process everything until checkboxes are added.... [behavior, behavior_videos, pophys]
        try:
            self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
            self.paramDict['WRname']            = self.WRName.toPlainText()  
            self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
            self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
            self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
            self.paramDict['notes']             = self.notes.toPlainText()
            self.paramDict['date']              = self.sessionDate.toPlainText()
            self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
            self.paramDict['pathToRawData']     = dataDir #'Y:/'
            self.paramDict['localPath']         = 'F:/BCI/'
            
            #open the window
            self.processingWindow = processingMouseWindow(self.threadingPool, self.paramDict)   # 1) create new winodw and pass params and threading pool
            self.runningWorkers.append(self.processingWindow)                                   # 2) put window object in runningWorkers list
            self.processingWindow.closeWindow.connect(self.removeMouseFromList)                 # 3) remove window object from runningWorkers list function for when window closes
            self.processingMouseList.addItem(
                self.processingWindow.windowTitle(), 
                os.path.dirname(os.path.abspath(__file__))[:-2] + 'imgs/processingIcon.png'     # 4) window is still open - put window title in the QList to keep track of and display status with icon
                )               
            self.processingWindow.show()                                                        # 5) show window and run worker

        except ValueError:                                                                      #if you forget to add data to a box or put letters where numbers should go
            err = QErrorMessage(self)
            err.showMessage('missing a field or incorrect datatype entry for one of the logging boxes')
            err.exec()
            return
        

    def removeMouseFromList(self, window):
        for i in range(self.processingMouseList.count()):
            if self.processingMouseList.item(i).text() == window.windowTitle():
                self.processingMouseList.takeItem(i)
                break
        self.processingMouseWindow.remove(window) 
    
    def mouseCompleteListUpdate(self,window):   
        for i in range(self.processingMouseList.count()): 
            if self.processsingMouseList.item(i).text() == window.windowTitle(): 
                self.processingMouseList.takeItem(i)
                self.processingMouseList.addItem(
                        self.processsingMouseList.item(i).text() , 
                        os.path.dirname(os.path.abspath(__file__))[:-2] + 'imgs/check-mark-icon-vector.jpg'     # 4) window is still open - put window title in the QList to keep track of and display status with icon
                        )
                break               
    # def copyToScratch(self):
    #     self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
    #     self.paramDict['WRname']            = self.WRName.toPlainText()  
    #     self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
    #     self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
    #     self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
    #     self.paramDict['notes']             = self.notes.toPlainText()
    #     self.paramDict['date']              = self.sessionDate.toPlainText()
    #     self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
    #     self.paramDict['pathToRawData']     = dataDir #'Y:/'
    #     self.paramDict['localPath']         = 'F:/BCI/'
        
    #     #set up signals
    #     signals = WorkerSignals()
    #     signals.nextStep.connect(self.onNextStep)
    #     signals.stepComplete.connect(self.onStepComplete)
    #     signals.allComplete.connect(self.onFullCompletion)
    #     signals.transmitData.connect(self.onDataTransmission)
    #     signals.error.connect(self.onError)
    #     self.threadingPool.start(transferToScratchWorker(signals, self.paramDict))
        
    # def initiatePipeline(self):
    #     print('INITIATING PIPELINE HERE ------------------------------------')
    #     #load textboxes into dictionary to give to worker
    #     self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
    #     self.paramDict['WRname']            = self.WRName.toPlainText()  
    #     self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
    #     self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
    #     self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
    #     self.paramDict['notes']             = self.notes.toPlainText()
    #     self.paramDict['date']              = self.sessionDate.toPlainText()
    #     self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
    #     self.paramDict['pathToRawData']     = dataDir #'Y:/'
    #     self.paramDict['localPath']         = 'F:/BCI/'

    #     #set up signals
    #     signals = WorkerSignals()
    #     signals.nextStep.connect(self.onNextStep)
    #     signals.stepComplete.connect(self.onStepComplete)
    #     signals.allComplete.connect(self.onFullCompletion)
    #     signals.transmitData.connect(self.onDataTransmission)
    #     signals.error.connect(self.onError)

    #     #send off worker to do its thing
    #     self.threadingPool.start(metaDataWorker(signals, self.paramDict))

    # #Worker Functions
    # def onNextStep(self, message):
    #     self.statusList.addItem(message)
    #     self.statusList.scrollToBottom()
    # def onStepComplete(self, message):
    #     self.statusList.addItem(message)
    #     self.statusList.scrollToBottom()
    # def onFullCompletion(self, message):
    #     self.statusList.addItem(message)
    #     self.statusList.scrollToBottom()
    # def onError(self, message):
    #     self.statusList.addItem(message)
    #     self.statusList.scrollToBottom()
    #     traceback.print_exc() 
    #     err = QErrorMessage(self)
    #     err.showMessage(message)
    #     err.exec()
    # def onDataTransmission(self, messageTuple):
    #     self.updateMouseSelectionDropdown()
    #     self.updateDatesDropdown()
    #     mouse, date = messageTuple
    #     index = self.mouseDateDropdown.findText(date)
    #     if index != -1:
    #         self.statusList.addItem(f'Showing PDFs for {mouse}')
    #         self.mouseDateDropdown.setCurrentIndex(index)
    #Back to app functions

    def sendToCloud(self):
        # import yaml
        
        #changing this path to be scratch instead of F:/Staging
        self.dataPathEntry = f"Y:/{self.WRName.toPlainText()}/{self.sessionDate.toPlainText()}"
        with open(self.dataPathEntry + '/session.json', 'r') as f:
          sessionParams = json.load(f)
        print(sessionParams['session_start_time'])
        
        try:
            self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
            self.paramDict['WRname']            = self.WRName.toPlainText()  
            self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
            self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
            self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
            self.paramDict['notes']             = self.notes.toPlainText()
            self.paramDict['date']              = self.sessionDate.toPlainText()
            self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
            self.paramDict['pathToRawData']     = dataDir #'Y:/'
            self.paramDict['localPath']         = 'F:/BCI/'
            self.paramDict['sessionStart'] = sessionParams['session_start_time']
            
            #set up signals
            signals = WorkerSignals()
            signals.nextStep.connect(self.onNextStep)
            signals.stepComplete.connect(self.onStepComplete)
            signals.allComplete.connect(self.onFullCompletion)
            signals.transmitData.connect(self.onDataTransmission)
            signals.error.connect(self.onError)
            
            #send off worker to do its thing
            self.threadingPool.start(cloudTransferWorker(signals, self.paramDict))
            
            
        except Exception:
            err = QErrorMessage(self)
            traceback.print_exc() 
            err.showMessage('Issue sending off data to aws... check your data')
            err.exec()
    
    def updateMouseSelectionDropdown(self):
        self.miceAvailable = glob( 'Y:/*')
        print(self.miceAvailable)
        mice = []
        for file in self.miceAvailable:
            if os.path.isdir(file):
                mouseWRname = file.split('/')[-1]
                print(mouseWRname)
                if mouseWRname.count('_')>1:
                    mice.append('_'.join(mouseWRname.split('_')[:-1]))
                else:
                    mice.append(mouseWRname.split('_')[0])
        uniqueMice = np.unique(mice)
        try: # if we have a mouse selected already, go back to it!
            currentindex = np.where(self.WRName.toPlainText()==uniqueMice)[0][0]
        except:
            currentindex  = 0        
        self.mouseNameDropDown.clear()
        for mouse in uniqueMice:
            self.mouseNameDropDown.addItem(f'{mouse}')
        self.mouseNameDropDown.setCurrentIndex(currentindex)

    def selectionChanged(self, index):
        self.datesDropDownActive = True
        self.selectedMouse = self.mouseNameDropDown.currentText()
        self.WRName.setPlainText(self.selectedMouse)
        # self.selectedPaths = glob(f'Y:/{self.selectedMouse}/*2*')
        self.selectedPaths = []
        for date in os.listdir(f'Y:/{self.selectedMouse}/'):
            try: 
                self.selectedPaths.append(  datetime.strptime(date, '%m%d%y')) #put dates in datetime format
            except Exception:
                #ignore improperly logged data
                pass
        self.datesToLook = [date.strftime('%m%d%y') for date in sorted(self.selectedPaths, reverse=True)] #sort dates and only return valid dates in order 
        self.updateDatesDropdown()
        self.WRName.setPlainText(self.selectedMouse)
    
    def updateDatesDropdown(self):
        if self.datesDropDownActive and len(self.datesToLook)>=1:
            self.mouseDateDropdown.clear()
            for dateFilePath in self.datesToLook:
                self.mouseDateDropdown.addItem(f'{dateFilePath}')
            self.mouseDateDropdown.setEnabled(self.datesDropDownActive)
        else:
            err = QErrorMessage(self)
            err.showMessage('Missing Logging Data for Session! Check Text Boxes')
            err.exec()

    def leftPageFunc(self):
        if self.pageSelect == 1:
            self.pageSelect = 1
            print('Page 1')
        else:
            self.pageSelect = self.pageSelect - 1
            print(f'Page {self.pageSelect}')
        self.loadPDF()
    
    def rightPageFunc(self):
        if self.pageSelect == 3:
            self.pageSelect = 3
            print('Page 3')
        else:
            self.pageSelect = self.pageSelect + 1
            print(f'Page {self.pageSelect}')
        self.loadPDF()

    def loadPDF(self):
        #default to page 3 for ease of use
        sessionData_focus = self.mouseDateDropdown.currentText()
        if len(self.WRName.toPlainText()) >1 and len(self.mouseDateDropdown.currentText()) >1:
            #Set Date Field as Date of Session Looking at
            self.sessionDate.setPlainText(sessionData_focus)               
            fullPath = Path('Y:/').joinpath(f'{self.WRName.toPlainText()}/{sessionData_focus}') # 'Y:/path to PDF
            print(fullPath)
            if self.selectedMouse !=  '-':
              try:
                with open(fullPath.joinpath('session.json'), 'r') as f:
                    self.sessionJSON = json.load(f)
                #update the other text fields appropriately
                self.mouseID.setPlainText(str(self.sessionJSON['subject_id'])),
                self.imageWaveLength.setPlainText(str(self.sessionJSON['data_streams'][0]['light_sources'][0]['wavelength'])),
                self.imagingDepth.setPlainText(str(self.sessionJSON['data_streams'][1]['ophys_fovs'][0]['imaging_depth'])),
                self.experimenterName.setPlainText(str(self.sessionJSON['experimenter_full_name'][0])),
                self.notes.setPlainText(str(self.sessionJSON['notes']))
    
            
                doc = fitz.open(fullPath.joinpath('session_plots.pdf'))
                page1 = doc.load_page(0)
                page2 = doc.load_page(1)
                page3 = doc.load_page(2)
                pix1 = page1.get_pixmap()
                pix2 = page2.get_pixmap()
                pix3 = page3.get_pixmap()
                image1 = QImage(pix1.samples, pix1.width, pix1.height, pix1.stride, QImage.Format.Format_RGB888)
                scaledImage1 = image1.scaled(1000, 500)
                image2 = QImage(pix2.samples, (pix2.width), (pix2.height), pix2.stride, QImage.Format.Format_RGB888) #need to scale this to fit on screen
                scaledImage2 = image2.scaled(1000, 500)
                image3 = QImage(pix3.samples, pix3.width, pix3.height, pix3.stride, QImage.Format.Format_RGB888)
                # scaledImage3 = image3.scaled(600, 200)
                if self.pageSelect ==1:
                    pixmap1 = QPixmap.fromImage(scaledImage1)
                    self.pdfLoc.setPixmap(pixmap1)
                if self.pageSelect ==2:
                    pixmap2 = QPixmap.fromImage(scaledImage2)
                    self.pdfLoc.setPixmap(pixmap2)
                if self.pageSelect ==3:
                    pixmap3 = QPixmap.fromImage(image3)
                    self.pdfLoc.setPixmap(pixmap3)
              except Exception as e:
                  pass










if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainApp = BergamoDataViewer()
    # mainApp.showMax()
    sys.exit(app.exec())
