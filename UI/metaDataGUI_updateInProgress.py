#%%
import numpy as np
import sys, os, json, traceback
from glob import glob
from pathlib import Path
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QListWidget, 
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
    QThreadPool
)
from PyQt6.QtGui import (
    QImage, 
    QPixmap, 
)
from datetime import datetime, date
import fitz #PyMuPDF
from main_utility import *
from metaDataWorker import (
    WorkerSignals, 
    metaDataWorker, 
    transferToScratchWorker, 
    cloudTransferWorker
)

today = str(date.today())
print('Running Data Viewer on:', today)
dataDir = 'Y:/' 
h = 65      #height of text boxes
     

class BergamoDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Viewer')
        self.showMaximized()
        self.paramDict = {}
        self.miceAvailable = glob(dataDir+'*') 
        self.listOfMice = os.listdir(dataDir)
        self.selectedPaths=None
        self.datesToLook= []
        self.datesDropDownActive = False
        self.selectedMouse = None
        self.pageSelect = 3
        self.dataPathEntry = None
        self.localDataStorage = None
        self.threadingPool = QThreadPool()
        self.initUI()

    def initUI(self):

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)
        exit_button = QPushButton('Exit')
        exit_button.clicked.connect(self.close)
        mainLayout.addWidget(exit_button)
        
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
        print(uniqueMice)
        for mouse in uniqueMice:
            self.mouseNameDropDown.addItem(f'{mouse}')
        self.mouseNameDropDown.setCurrentIndex(0)
        self.mouseNameDropDown.currentIndexChanged.connect(self.selectionChanged)

        #######################################################
        ############## Text Boxes #############################
        #######################################################

        self.mouseEntryLabel = QGroupBox('Mouse Info')
        self.mouseEntryLabel.setFixedHeight(450)
        
        self.mainMouseEntryLayout = QVBoxLayout()
        self.mouseEntryLayout_layer1 = QHBoxLayout()
        self.mouseEntryLayout_layer2 = QHBoxLayout()
        self.mouseEntryLayout_layer3 = QHBoxLayout()
        self.mouseEntryLayout_layer4 = QHBoxLayout()
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer1)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer2)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer3)
        self.mainMouseEntryLayout.addLayout(self.mouseEntryLayout_layer4)

        #For Status Updates
        self.statusList = QListWidget(self)
        self.mainMouseEntryLayout.addWidget(self.statusList)

        self.mouseEntryLabel.setLayout(self.mainMouseEntryLayout)
        
        #Layer 1
        self.WRName = highlightedTextEdit()                 
        self.WRName.tab.connect(self.tabToSwitch)               
        self.WRNameLabel = QGroupBox('Mouse WR Name')           
        self.WRNameLabel.setFixedHeight(h)                      
        self.WRNameLayout = QVBoxLayout()                       
        self.WRNameLayout.addWidget(self.WRName)                
        self.WRNameLabel.setLayout(self.WRNameLayout)           
        self.mouseEntryLayout_layer1.addWidget(self.WRNameLabel)
        
        self.mouseID = highlightedTextEdit() 
        self.mouseIDLabel = QGroupBox('Mouse ID')
        self.mouseIDLabel.setFixedHeight(h)
        self.mouseIDLayout = QVBoxLayout()
        self.mouseIDLayout.addWidget(self.mouseID)
        self.mouseIDLabel.setLayout(self.mouseIDLayout)
        self.mouseEntryLayout_layer1.addWidget(self.mouseIDLabel)
        
        #Layer 2
        self.imageWaveLength = highlightedTextEdit() 
        self.imageWaveLengthLabel = QGroupBox('Imaging Wavelength')
        self.imageWaveLengthLabel.setFixedHeight(h)
        self.imageWaveLengthLayout = QVBoxLayout()
        self.imageWaveLengthLayout.addWidget(self.imageWaveLength)
        self.imageWaveLengthLabel.setLayout(self.imageWaveLengthLayout)
        self.mouseEntryLayout_layer2.addWidget(self.imageWaveLengthLabel)
        
        self.imagingDepth = highlightedTextEdit()
        self.imagingDepthLabel = QGroupBox('Imaging Depth')
        self.imagingDepthLabel.setFixedHeight(h)
        self.imagingDepthLayout = QVBoxLayout()
        self.imagingDepthLayout.addWidget(self.imagingDepth)
        self.imagingDepthLabel.setLayout(self.imagingDepthLayout)
        self.mouseEntryLayout_layer2.addWidget(self.imagingDepthLabel)
        
        self.experimenterName = highlightedTextEdit()
        self.experimenterNameLabel = QGroupBox('Experimenter Name')
        self.experimenterNameLabel.setFixedHeight(h)
        self.experimenterNameLayout = QVBoxLayout()
        self.experimenterNameLayout.addWidget(self.experimenterName)
        self.experimenterNameLabel.setLayout(self.experimenterNameLayout)
        self.mouseEntryLayout_layer2.addWidget(self.experimenterNameLabel)
        
        self.sessionDate = highlightedTextEdit()
        self.sessionDate.setPlainText(today)
        self.sessionDateLabel = QGroupBox('Date of Session')
        self.sessionDateLabel.setFixedHeight(h)
        self.sessionDateLayout = QVBoxLayout()
        self.sessionDateLayout.addWidget(self.sessionDate)
        self.sessionDateLabel.setLayout(self.sessionDateLayout)
        self.mouseEntryLayout_layer2.addWidget(self.sessionDateLabel)
        
        self.targetStruct = highlightedTextEdit()
        self.targetStruct.setPlainText('Primary Motor Cortex')
        self.targetStructLabel = QGroupBox('Targeted Brain Structure')
        self.targetStructLabel.setFixedHeight(h)
        self.targetStructLayout = QVBoxLayout()
        self.targetStructLayout.addWidget(self.targetStruct)
        self.targetStructLabel.setLayout(self.targetStructLayout)
        self.mouseEntryLayout_layer3.addWidget(self.targetStructLabel)
    
        #Layer 4
        self.notes = highlightedTextEdit()
        self.notesLabel = QGroupBox('Session Notes')
        self.notesLabel.setFixedHeight(75)
        self.notesLayout = QVBoxLayout()
        self.notesLayout.addWidget(self.notes)
        self.notesLabel.setLayout(self.notesLayout)
        self.mouseEntryLayout_layer4.addWidget(self.notesLabel)

        #######################################################
        ##############  Buttons ###############################
        #######################################################

        self.transferDataToScratchButton = QPushButton('Transfer Data To Scratch')
        self.mainMouseEntryLayout.addWidget(self.transferDataToScratchButton)
        self.transferDataToScratchButton.clicked.connect(self.copyToScratch)
        self.processDataButton = QPushButton('Process Data')
        self.mainMouseEntryLayout.addWidget(self.processDataButton)
        self.processDataButton.clicked.connect(self.initiatePipeline)
        
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
        self.plotVisualizationLayout.addWidget(self.pdfLoc)
        self.plotVisualizationLayout.addWidget(self.sendToCloudButton)
        
        #######################################################
        ##############  Organize Layout #######################
        #######################################################

        mainLayout.addWidget(exit_button)
        mainLayout.addWidget(self.mouseNameDropDown)
        mainLayout.addWidget(self.mouseEntryLabel)
        mainLayout.addWidget(self.plotVisualizationLabel)
        self.textEdits = [
            self.WRName,
            self.mouseID,
            self.imageWaveLength,
            self.imagingDepth,
            self.experimenterName,
            self.sessionDate,
            self.targetStruct,
            self.notes
        ]
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
        if isinstance(widget, highlightedTextEdit):
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

    def copyToScratch(self):
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

        signals = WorkerSignals()
        signals.nextStep.connect(self.onNextStep)
        signals.stepComplete.connect(self.onStepComplete)
        signals.allComplete.connect(self.onFullCompletion)
        signals.transmitData.connect(self.onDataTransmission)
        signals.error.connect(self.onError)
        self.threadingPool.start(transferToScratchWorker(signals, self.paramDict))
        
    def initiatePipeline(self):
        print('INITIATING PIPELINE HERE ------------------------------------')

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

        signals = WorkerSignals()
        signals.nextStep.connect(self.onNextStep)
        signals.stepComplete.connect(self.onStepComplete)
        signals.allComplete.connect(self.onFullCompletion)
        signals.transmitData.connect(self.onDataTransmission)
        signals.error.connect(self.onError)

        self.threadingPool.start(metaDataWorker(signals, self.paramDict))

    def onNextStep(self, message):
        self.statusList.addItem(message)
        self.statusList.scrollToBottom()

    def onStepComplete(self, message):
        self.statusList.addItem(message)
        self.statusList.scrollToBottom()

    def onFullCompletion(self, message):
        self.statusList.addItem(message)
        self.statusList.scrollToBottom()

    def onError(self, message):
        self.statusList.addItem(message)
        self.statusList.scrollToBottom()
        traceback.print_exc() 
        err = QErrorMessage(self)
        err.showMessage(message)
        err.exec()
        
    def onDataTransmission(self, messageTuple):
        self.updateMouseSelectionDropdown()
        self.updateDatesDropdown()
        mouse, date = messageTuple
        index = self.mouseDateDropdown.findText(date)
        if index != -1:
            self.statusList.addItem(f'Showing PDFs for {mouse}')
            self.mouseDateDropdown.setCurrentIndex(index)

    def sendToCloud(self):
        self.dataPathEntry = f"Y:/{self.WRName.toPlainText()}/{self.sessionDate.toPlainText()}"
        with open(self.dataPathEntry + '/session.json', 'r') as f:
          sessionParams = json.load(f)
        
        try:
            self.paramDict['subjectID']         = str(self.mouseID.toPlainText())
            self.paramDict['WRname']            = self.WRName.toPlainText()  
            self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
            self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
            self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
            self.paramDict['notes']             = self.notes.toPlainText()
            self.paramDict['date']              = self.sessionDate.toPlainText()
            self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
            self.paramDict['pathToRawData']     = dataDir 
            self.paramDict['localPath']         = 'F:/BCI/'
            self.paramDict['sessionStart'] = sessionParams['session_start_time']

            signals = WorkerSignals()
            signals.nextStep.connect(self.onNextStep)
            signals.stepComplete.connect(self.onStepComplete)
            signals.allComplete.connect(self.onFullCompletion)
            signals.transmitData.connect(self.onDataTransmission)
            signals.error.connect(self.onError)

            self.threadingPool.start(cloudTransferWorker(signals, self.paramDict))
            
            
        except Exception:
            err = QErrorMessage(self)
            traceback.print_exc() 
            err.showMessage('Issue sending off data to aws... check your data')
            err.exec()
    
    def updateMouseSelectionDropdown(self):
        self.miceAvailable = glob( 'Y:/*')#self.paramDict['stagingDir'] +'/*')
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
        try:
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
        self.selectedPaths = []
        for date in os.listdir(f'Y:/{self.selectedMouse}/'):
            try: 
                self.selectedPaths.append(  datetime.strptime(date, '%m%d%y')) #put dates in datetime format
            except Exception:
                pass
        self.datesToLook = [date.strftime('%m%d%y') for date in sorted(self.selectedPaths, reverse=True)]
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
        sessionData_focus = self.mouseDateDropdown.currentText()
        if len(self.WRName.toPlainText()) >1 and len(self.mouseDateDropdown.currentText()) >1:
            self.sessionDate.setPlainText(sessionData_focus)               
            fullPath = Path('Y:/').joinpath(f'{self.WRName.toPlainText()}/{sessionData_focus}')
            print(fullPath)
            if self.selectedMouse !=  '-':
              try:
                with open(fullPath.joinpath('session.json'), 'r') as f:
                    self.sessionJSON = json.load(f)
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
                image2 = QImage(pix2.samples, (pix2.width), (pix2.height), pix2.stride, QImage.Format.Format_RGB888) #need to scale this to fit on screen
                scaledImage2 = image2.scaled(700, 800)
                image3 = QImage(pix3.samples, pix3.width, pix3.height, pix3.stride, QImage.Format.Format_RGB888)
                if self.pageSelect ==1:
                    pixmap1 = QPixmap.fromImage(image1)
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
    sys.exit(app.exec())
