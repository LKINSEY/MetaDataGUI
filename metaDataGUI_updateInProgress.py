# from main_utility import *
#%%
from PyQt6.QtGui import QPixmap
import numpy as np
import sys, zmq, os, subprocess, queue, json, shutil, traceback
from glob import glob
import matplotlib.pyplot as plt
import socket as skt
from pathlib import Path
from datetime import datetime, date
from PyQt6.QtWidgets import  QScrollArea, QListWidget, QMenuBar, QTabWidget, QCheckBox, QPushButton, QComboBox, QLineEdit, QHBoxLayout, QLabel, QErrorMessage, QApplication, QMenuBar, QMenu, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QGroupBox, QInputDialog, QFileDialog
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QThreadPool
from PyQt6.QtGui import QIntValidator, QAction, QImage, QPixmap, QColor, QPalette, QMovie
from PyQt6.QtWidgets import  QMenuBar, QLineEdit, QHBoxLayout, QLabel, QErrorMessage, QApplication, QMenuBar, QMenu, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QGroupBox, QInputDialog, QFileDialog
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import fitz #PyMuPDF
#comment out for testing
from aind_metadata_mapper.bergamo.session import ( BergamoEtl, 
                                                  JobSettings,
                                                  RawImageInfo,
                                                  )
import bergamo_rig
from main_utility import *
from metaDataWorker import WorkerSignals, metaDataWorker, transferToScratchWorker, cloudTransferWorker

today = str(date.today())
print('Running Data Viewer on:', today)
dataDir = 'Y:/' #setting to scratch save location
# dataDir = 'F:/Staging'
# dataDir = 'F:/BCI
# dataDir = 'Z:/ophys/Lucas/BCI_upload_GUI/exampleData'



#Creating a seperate class that can help user verify what boxes are valid by just clicking on them
class userValidatableTextEdit(QTextEdit):
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
        



class BergamoDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Viewer')
        self.showMaximized()
        #Define Init Variables
        self.paramDict = {}
        self.miceAvailable = glob('Y:/*') #glob('F:/staging/*') #refreshes every time you start the app
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
        
        #fixed height for entry boxes
        h = 65
        
        #Setting Central Widget
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        
        #defining the background layout everything will be put in vertically
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)
        
        #Fun easter egg
        self.movie = QMovie('C:/temp/pulp-fiction-wtf.gif')
        
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
                if 'B' in mouseWRname or 'C' in mouseWRname or 'p' in mouseWRname: #mouseWRname.count('_')>=1:
                    mice.append(mouseWRname)#mouseWRname.split('_')[0])
                    # print(mouseWRname, mouseWRname.count('_'), mouseWRname.split('_')[0])
        uniqueMice = np.unique(mice)
        for mouse in uniqueMice:
            self.mouseNameDropDown.addItem(f'{mouse}')
        self.mouseNameDropDown.setCurrentIndex(0)
        self.mouseNameDropDown.currentIndexChanged.connect(self.selectionChanged)
        
        self.newMouseCheck = QCheckBox('Check this if entering info for new mouse')
        self.newMouseCheck.stateChanged.connect(self.highlightTextBoxes)
        

        #######################################################
        ############## Entry Info Here ########################
        #######################################################
        
        #If Entering a new mouse, just enter ID here first 
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
        
        self.WRName = userValidatableTextEdit()                 #Define Edit
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
        
        #Layer 3
        # self.scratchLoc = userValidatableTextEdit()
        # self.scratchLoc.setPlainText('//allen/aind/scratch/2p-working-group/data-uploads')
        # self.scratchLocLabel = QGroupBox('Scratch Save Location')
        # self.scratchLocLabel.setFixedHeight(h)
        # self.scratchLocLayout = QVBoxLayout()
        # self.scratchLocLayout.addWidget(self.scratchLoc)
        # self.scratchLocLabel.setLayout(self.scratchLocLayout)
        # self.mouseEntryLayout_layer3.addWidget(self.scratchLocLabel)
        
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


        #putting a "transfer local data to scratch" button here
        self.transferDataToScratchButton = QPushButton('Transfer Data To Scratch')
        self.mainMouseEntryLayout.addWidget(self.transferDataToScratchButton)
        self.transferDataToScratchButton.clicked.connect(self.copyToScratch)
        
        
        #Process Data Button goes after data is entered
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
        
        #Define the order things are placed
        #Main Layout --> QVBoxLayout
        mainLayout.addWidget(exit_button)
        mainLayout.addWidget(self.mouseNameDropDown)
        mainLayout.addWidget(self.newMouseCheck)
        mainLayout.addWidget(self.mouseEntryLabel)
        mainLayout.addWidget(self.plotVisualizationLabel)
        
        self.initializeGUI()
        self.show()
    
        #######################################################
        ##############  FUN-ctions ############################
        #######################################################
        
    def initializeGUI(self):
        self.pdfLoc.setMovie(self.movie)
        self.movie.start()
        # self.resize(self.movie.currentImage().size())
        
    def highlightTextBoxes(self):
        #we want to make all of the text boxes green until a user clicks in them, puts text there, then clicks out
        #this function will also activate when a new mouse is selected from drop down so that a user
        #verifies that each item in each text box is correct
        isCheckedFlag = self.newMouseCheck.isChecked()
        if isCheckedFlag:
            self.WRName.setColorToGreen()               #setStyleSheet(f'background-color: {textEditColor.name()}')
            self.mouseID.setColorToGreen()              #setStyleSheet(f'background-color: {textEditColor.name()}')
            self.imageWaveLength.setColorToGreen()
            self.imagingDepth.setColorToGreen()
            self.experimenterName.setColorToGreen()
            self.sessionDate.setColorToGreen()
            self.scratchLoc.setColorToGreen()
            self.targetStruct.setColorToGreen()
            self.notes.setColorToGreen()
        else:
            self.WRName.setDefaultColor()
            self.mouseID.setDefaultColor()
            self.imageWaveLength.setDefaultColor()
            self.imagingDepth.setDefaultColor()
            self.experimenterName.setDefaultColor()
            self.sessionDate.setDefaultColor()
            self.scratchLoc.setDefaultColor()
            self.targetStruct.setDefaultColor()
            self.notes.setDefaultColor()
    
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
    def copyToScratch(self):
        self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
        self.paramDict['WRname']            = self.WRName.toPlainText()  
        self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
        self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
        self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
        self.paramDict['notes']             = self.notes.toPlainText()
        # self.paramDict['stagingDir']        = 'F:/Staging' #no longer local storage
        self.paramDict['date']              = self.sessionDate.toPlainText()
        # self.paramDict['scratchLocation']   = self.scratchLoc.toPlainText()
        self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
        self.paramDict['pathToRawData']     = dataDir #'Y:/'
        self.paramDict['localPath']         = 'F:/BCI/'
        
        #set up signals
        signals = WorkerSignals()
        signals.nextStep.connect(self.onNextStep)
        signals.stepComplete.connect(self.onStepComplete)
        signals.allComplete.connect(self.onFullCompletion)
        signals.transmitData.connect(self.onDataTransmission)
        signals.error.connect(self.onError)
        
        self.threadingPool.start(transferToScratchWorker(signals, self.paramDict))
        
    def initiatePipeline(self):
        print('INITIATING PIPELINE HERE ------------------------------------')
        #load textboxes into dictionary to give to worker
        self.paramDict['subjectID']         = int(self.mouseID.toPlainText())
        self.paramDict['WRname']            = self.WRName.toPlainText()  
        self.paramDict['wavelength']        = int(self.imageWaveLength.toPlainText())
        self.paramDict['imagingDepth']      = int(self.imagingDepth.toPlainText())
        self.paramDict['experimenterName']  = self.experimenterName.toPlainText()
        self.paramDict['notes']             = self.notes.toPlainText()
        # self.paramDict['stagingDir']        = 'F:/Staging' #no longer local storage
        self.paramDict['date']              = self.sessionDate.toPlainText()
        # self.paramDict['scratchLocation']   = self.scratchLoc.toPlainText()
        self.paramDict['targetedStructure'] = self.targetStruct.toPlainText()
        self.paramDict['pathToRawData']     = dataDir #'Y:/'
        self.paramDict['localPath']         = 'F:/BCI/'

        #set up signals
        signals = WorkerSignals()
        signals.nextStep.connect(self.onNextStep)
        signals.stepComplete.connect(self.onStepComplete)
        signals.allComplete.connect(self.onFullCompletion)
        signals.transmitData.connect(self.onDataTransmission)
        signals.error.connect(self.onError)

        #send off worker to do its thing
        self.threadingPool.start(metaDataWorker(signals, self.paramDict))

    #Worker Functions
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
            self.statusLust.addItem('Showing PDFs')
            self.combo_box.setCurrentIndex(index)
            # self.loadPDF() # does the changing of the date index activate loadPDF?? lets find out
    
    #Back to app functions

    def sendToCloud(self):
        # import yaml
        
        #changing this path to be scratch instead of F:/Staging
        self.dataPathEntry = f"Y:/{self.WRName.toPlainText()}/{self.sessionDate.toPlainText()}"
        print(self.dataPathEntry)
        
        try:
            # behavior_folder_staging = Path.joinpath(Path(self.dataPathEntry),Path('behavior'))
            # behavior_video_folders = Path.joinpath(Path(self.dataPathEntry),Path('behavior_video'))
            # md = load_metadata_from_folder(self.dataPathEntry)
            # session_folder = self.localDataStorage
            # session_dict  ={'acquisition_datetime':datetime.fromisoformat(md['session']['session_start_time']), # from tiff files
            #                 'capsule_id': '2103f231-8eec-45eb-bc54-c776dc33a0a7', # to trigger capsule
            #                 'destination': self.scratchLoc.toPlainText(),
            #                 'modalities': {'behavior':[str(behavior_folder_staging)], # paths to folder/file
            #                             'pophys':[str(session_folder)],# paths to folder/file
            #                             'behavior-videos':[str(behavior_video_folders)]},
            #                 'mount': 'single-plane-ophys_731012_2024-08-13_23-49-46', #
            #                 'name': 'bergamo_raw_{}_{}'.format(str(self.sessionData['subject_id']),datetime.fromisoformat(md['session']['session_start_time']).date()),#
            #                 'platform': 'single-plane-ophys',
            #                 'processor_full_name': str(self.sessionData['experimenter_full_name'][0]), #'experimenter name'
            #                 'project_name': 'Brain Computer Interface',
            #                 's3_bucket': 'private', #'scratch'
            #                 #'schedule_time': None,#should be NOW2024-06-22 03:00:00
            #                 'schemas': [str(Path(self.dataPathEntry).joinpath('session.json')),
            #                             str(Path(self.dataPathEntry).joinpath('rig.json'))],#list of strings of paths to rig and session jsons'
            #                 'subject_id': int(self.sessionData['subject_id']),
            #             }

            # # with open(Path('F:/Staging/').joinpath(Path('manifest_{}.yml'.format(Path(self.dataPathEntry).name))),'w') as yam:
            # #     yaml.dump(session_dict,yam)

            # with open(Path('C:/Users/ScanImage/aind_watchdog_service/manifests/').joinpath(Path('manifest_{}.yml'.format(Path(self.dataPathEntry).name))),'w') as yam:
            #     yaml.dump(session_dict,yam)
            
            
            ## Fun alternative: don't be fancy, just immediatly upload to s3
            session_dict  ={'acquisition_datetime':datetime.fromisoformat(md['session']['session_start_time']), # from tiff files
                            'capsule_id': '2103f231-8eec-45eb-bc54-c776dc33a0a7', # to trigger capsule
                            'destination': self.dataPathEntry,
                            'modalities': {'behavior':[str(behavior_folder_staging)], # paths to folder/file
                                        'pophys':[str(session_folder)],# paths to folder/file
                                        'behavior-videos':[str(behavior_video_folders)]},
                            'mount': 'single-plane-ophys_731012_2024-08-13_23-49-46', #
                            'name': 'bergamo_raw_{}_{}'.format(str(self.sessionData['subject_id']),datetime.fromisoformat(md['session']['session_start_time']).date()),#
                            'platform': 'single-plane-ophys',
                            'processor_full_name': str(self.sessionData['experimenter_full_name'][0]), #'experimenter name'
                            'project_name': 'Brain Computer Interface',
                            's3_bucket': 'private', #'scratch'
                            #'schedule_time': None,#should be NOW2024-06-22 03:00:00
                            'schemas': [str(Path(self.dataPathEntry).joinpath('session.json')),
                                        str(Path(self.dataPathEntry).joinpath('rig.json'))],#list of strings of paths to rig and session jsons'
                            'subject_id': int(self.sessionData['subject_id']),
                        }
            
            #set up signals
            signals = WorkerSignals()
            signals.nextStep.connect(self.onNextStep)
            signals.stepComplete.connect(self.onStepComplete)
            signals.allComplete.connect(self.onFullCompletion)
            signals.transmitData.connect(self.onDataTransmission)
            signals.error.connect(self.onError)
            
            #send off worker to do its thing
            self.threadingPool.start(cloudTransferWorker(signals, self.session_dict, self.sessionData['subject_id']))
            
            
        except Exception:
            err = QErrorMessage(self)
            err.showMessage('Could not generate YAML')
            err.exec()
    
    def updateMouseSelectionDropdown(self):
        self.miceAvailable = glob( 'Y:/*2*')#self.paramDict['stagingDir'] +'/*')
        mice = []
        for file in self.miceAvailable:
            if os.path.isdir(file):
                mouseWRname = file.split('\\')[-1]
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
        self.selectedPaths = glob(f'Y:/{self.selectedMouse}/*2*') #f'F:/Staging/{self.selectedMouse}*') #change this to scratch
        self.datesToLook = [(file.split('\\')[-1]).split('_')[-1] for file in self.selectedPaths]
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
            fullPath = Path('F:/Staging/').joinpath(f'{self.WRName.toPlainText()}_{sessionData_focus}') # 'Y:/path to PDF
            print(fullPath)
            if self.selectedMouse !=  '-':
                with open(fullPath.joinpath('session.json'), 'r') as f:
                    self.sessionJSON = json.load(f)
                #update the other text fields appropriately
                self.mouseID.setPlainText(str(self.sessionJSON['subject_id'])),
                self.imageWaveLength.setPlainText(str(self.sessionJSON['data_streams'][0]['light_sources'][0]['wavelength'])),
                self.imagingDepth.setPlainText(str(self.sessionJSON['data_streams'][1]['ophys_fovs'][0]['imaging_depth'])),
                self.experimenterName.setPlainText(str(self.sessionJSON['experimenter_full_name'][0])),
                self.notes.setPlainText(str(self.sessionJSON['notes']))
    
            try:
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
                err = QErrorMessage(self)
                traceback.print_exc() 
                err.showMessage('Refusing to load PDF because PDF does not have all of the necessary pages...')
                err.exec()









if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainApp = BergamoDataViewer()
    # mainApp.showMax()
    sys.exit(app.exec())
