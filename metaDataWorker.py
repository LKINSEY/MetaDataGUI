from PyQt6.QtCore import QRunnable, pyqtSignal, QObject, QThreadPool
import traceback, os, json, traceback, shutil
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date
from aind_metadata_mapper.bergamo.session import ( BergamoEtl, 
                                                  JobSettings,
                                                  RawImageInfo,
                                                  )
import bergamo_rig

#from REST API documentation
from aind_data_transfer_service.configs.job_configs import ModalityConfigs, BasicUploadJobConfigs
from pathlib import PurePosixPath
import json
import requests
from aind_data_transfer_models.core import ModalityConfigs, BasicUploadJobConfigs, SubmitJobRequest
from aind_data_schema_models.modalities import Modality
from aind_data_schema_models.platforms import Platform
######################################################

from main_utility import *


class WorkerSignals(QObject):
    stepComplete = pyqtSignal(str)      #emits a message to be read out in QListWidget before and afterevery function
    nextStep = pyqtSignal(str)          #emits same as stepComplete, but will call a diff function to put diff stuff in list widget
    allComplete = pyqtSignal()          #just a way of app to know everything is done and pdfs can be displayed
    transmitData = pyqtSignal(tuple)
    error = pyqtSignal(str)
    
class metaDataWorker(QRunnable):
    def __init__(self, signals, paramDict):
        super().__init__()
        self.signals = signals
        self.params = paramDict
        self.sessionData = {}
        self.mouseDict = {}
    
    def run(self):
        
        # #error condition - missing text entery
        # for key in self.params:
        #     if not isinstance(self.params.get(key, ''), (list, str)) or len(str(self.params.get(key, '')))<2:
        #         self.signals.error.emit('Missing Field Name - aborting process')
        #         return

        #Load Init JSON and mouseDict JSON and establish data paths
        WRname = self.params.get('WRname')
        dateEnteredAs = self.params.get('date')
        try:
            dateTimeObj = datetime.strptime(dateEnteredAs,'%Y-%m-%d').date()
            dateFileFormat = dateTimeObj.strftime('%m%d%y') #mmddyy]
        except ValueError:
            dateFileFormat = str(dateEnteredAs) #already entered as mmddyy
        
        #I want the staging directory to be the scratch location, saved in mouse-->date-->data format, then in the mouse/date/ file, we can have actual behavior data
        stagingDir = 'Y:/'  #self.params.get('stagingDir') #will contain the init.json and mouseDict.json
        sessionFolder = Path(self.params.get('pathToRawData') + f'/{WRname}/{dateFileFormat}') #this is same thing as above... but keeping it to change minimal code

        with open(Path(stagingDir + '/init.json'), 'r') as f:
            self.sessionData = json.load(f)
        with open(Path(stagingDir + '/mouseDict.json'), 'r') as f:
            self.mouseDict = json.load(f)
        
        self.sessionData['subject_id']                                          = self.params.get('subjectID')
        self.sessionData['data_streams'][0]['light_sources'][0]['wavelength']   = self.params.get('wavelength')
        self.sessionData['data_streams'][1]['ophys_fovs'][0]['imaging_depth']   = self.params.get('imagingDepth')
        self.sessionData['experimenter_full_name'][0]                           = self.params.get('experimenterName')
        self.sessionData['notes']                                               = self.params.get('notes')

        #### LOGGING PIPELINE ####
        #Step 1: check if mouse name and id is in dictionary
        #quick check for a typo
        if '/' in WRname or ' ' in WRname:
            self.signals.error.emit('Error in typing WR Name, either a tab, enter, or space was pressed -- aborting process')
            return
        if WRname in self.mouseDict:
            self.signals.stepComplete.emit(f'{WRname} is an existing mouse')
        else:
            self.signals.stepComplete.emit(f'{WRname} is a new mouse, logging in dictionary')
            self.mouseDict[WRname] = self.params.get('subjectID')
            with open(Path(stagingDir + '/mouseDict.json'), 'w') as f:
                json.dump(self.mouseDict, f)
        
        #Step 2: check if sessionFolder exists
        stagingMouseSessionPath = f'Y:/{WRname}/{dateFileFormat}/'#turned into scratch location             #Path(stagingDir).joinpath( Path(f'{WRname}_{dateEnteredAs}'))
        
        if os.path.exists(sessionFolder):  #~os.path.exists(stagingMouseSessionPath) and os.path.exists(sessionFolder): #check if behavior folders have been processed
            
            #Step 3: Make folders for each of the behavior types
            Path(stagingMouseSessionPath).mkdir(parents=True, exist_ok=True)                                    # makes mouse staging folder F:/staging/mouseWRname_mm-dd-yyyy
            behavior_folder_staging = Path.joinpath(Path(stagingMouseSessionPath),Path('behavior'))
            behavior_video_folder_staging = Path.joinpath(Path(stagingMouseSessionPath),Path('behavior_video'))
            Path(behavior_folder_staging).mkdir(parents=True, exist_ok=True)                                    # puts behavior folder in staging folder
            Path(behavior_video_folder_staging).mkdir(parents=True, exist_ok=True)                              # puts behavior video folder in staging folder
            #let us know
            self.signals.stepComplete.emit('Staging Folders Created')


        else:
            if ~os.path.exists(stagingMouseSessionPath):
                self.signals.error.emit('Session Folder Specified does not exist -- aborting process')
            else:
                self.signals.error.emit('Staging Directory not found -- aborting process')
            return

        #Step 4: run extract_behavior using raw data found in sessionFolder

        try:
            self.signals.nextStep.emit('Extracting Behavior')
            rc = extract_behavior(WRname, sessionFolder, behavior_folder_staging)
            behavior_fname = f"{Path(sessionFolder).name}-bpod_zaber.npy"
            self.signals.stepComplete.emit('Behavior Data Extracted Successfully')
        except Exception:
            self.signals.error.emit('Error extracting behavior -- check traceback -- aborting process')
            traceback.print_exc() 
            return

        #Step 5: Generate Rig JSON
        try:
            self.signals.nextStep.emit('Generating Rig JSON')
            rig_json = bergamo_rig.generate_rig_json()
            with open(Path(stagingMouseSessionPath).joinpath(Path('rig.json')), 'w') as json_file:
                json_file.write(rig_json)
            self.signals.stepComplete.emit('Rig JSON Created Successfully!')
        except Exception:
            self.signals.error.emit('Error generating rig json -- check traceback -- aborting process')
            traceback.print_exc() 
            return
        
        #Step 6: Generate Session JSON
        try:
            self.signals.nextStep.emit('Generating Session JSON')
            behavior_data, hittrials, goodtrials, behavior_task_name, is_side_camera_active, is_bottom_camera_active = prepareSessionJSON(behavior_folder_staging, behavior_fname)
            user_settings = JobSettings(    input_source                = Path(sessionFolder),
                                            output_directory            = Path(stagingMouseSessionPath),
                                            experimenter_full_name      = [str(self.sessionData['experimenter_full_name'][0])],
                                            subject_id                  = str(int(self.sessionData['subject_id'])),
                                            imaging_laser_wavelength    = int(self.sessionData['data_streams'][0]['light_sources'][0]['wavelength']),
                                            fov_imaging_depth           = int(self.sessionData['data_streams'][1]['ophys_fovs'][0]['imaging_depth']),
                                            fov_targeted_structure      = self.params.get('targetedStructure'), 
                                            notes                       = str(self.sessionData['notes']),
                                            session_type                = "BCI",
                                            iacuc_protocol              = "2109",
                                            rig_id                      = "442_Bergamo_2p_photostim",
                                            behavior_camera_names       = np.asarray(["Side Face Camera","Bottom Face Camera"])[np.asarray([is_side_camera_active,is_bottom_camera_active])].tolist(),
                                            imaging_laser_name          = "Chameleon Laser",
                                            photostim_laser_name        = "Monaco Laser",
                                            photostim_laser_wavelength  =  1035,
                                            starting_lickport_position  = [ 0,
                                                                            -1*np.abs(np.median(behavior_data['zaber_reward_zone']-behavior_data['zaber_limit_far'])),
                                                                            0],
                                            behavior_task_name          = behavior_task_name,
                                            hit_rate_trials_0_10        = np.nanmean(hittrials[goodtrials][:10]),
                                            hit_rate_trials_20_40       = np.nanmean(hittrials[goodtrials][20:40]),
                                            total_hits                  = sum(hittrials[goodtrials]),
                                            average_hit_rate            = sum(hittrials[goodtrials])/sum(goodtrials),
                                            trial_num                   = sum(goodtrials))
            etl_job = BergamoEtl(job_settings=user_settings,)
            session_metadata = etl_job.run_job()
            self.signals.stepComplete.emit('Session JSON Created Successfully!')
        except Exception:
            self.signals.error.emit('Error generating session json -- check traceback -- aborting process')
            traceback.print_exc() 
            return
        #Step 7: Stage Videos
        try:
            self.signals.nextStep.emit('Staging Videos')
            stagingVideos(behavior_data, behavior_video_folder_staging)
            self.signals.stepComplete.emit('Video Staged Successfully!')
        except Exception:
            self.signals.error.emit('Error Staging Videos -- check traceback -- aborting process')
            traceback.print_exc() 
            pass
        #Step 8: Create and display PDFs
        try:
            self.signals.nextStep.emit('Making PDFs')
            createPDFs(stagingMouseSessionPath, behavior_data, str(self.sessionData['subject_id']), dateEnteredAs)
            self.signals.stepComplete.emit('PDFs Successfully Made!')
        except Exception:
            self.signals.error.emit('Error Generating PDFs -- check traceback -- aborting process')
            traceback.print_exc() 
            return

        #Complete!
        self.signals.transmitData.emit( (WRname, dateEnteredAs))
        self.signals.allComplete.emit('Ready for YML Confirmation')
        return




class transferToScratchWorker(QRunnable):
    def __init__(self, signals, pathDict):
        super().__init__()
        self.signals = signals
        self.params = pathDict
    
    def run(self):
        startTime = datetime.now()
        localPath = self.params.get('localPath')
        scratchPath = self.params.get('pathToRawData')
        thisMouse = self.params.get('WRname')
        dateEnteredAs = self.params.get('date')
        try:
            dateTimeObj = datetime.strptime(dateEnteredAs,'%Y-%m-%d').date()
            dateFileFormat = dateTimeObj.strftime('%m%d%y') #mmddyy]
        except ValueError:
            dateFileFormat = str(dateEnteredAs) #already entered as mmddyy
        sourceDir = localPath+f'/{thisMouse}/{dateFileFormat}'
        destinationDir = scratchPath+f'/{thisMouse}/{dateFileFormat}/pophys'
        self.signals.nextStep.emit('Copying Raw Data To Scratch - Transfer Worker')
        
        if not os.path.exists(destinationDir):
            shutil.copytree(sourceDir, destinationDir)
            finishTime = datetime.now()
            deltaT = (finishTime - startTime)#.strftime('%H:%M:%S.%f')
            self.signals.nextStep.emit('Data Successfully copied to scratch')
            self.signals.nextStep.emit(f'This took: {deltaT}')
        else:
            self.signals.nextStep.emit('Data Already Exists on Scratch')
            finishTime = datetime.now()
            deltaT = (finishTime - startTime)#.strftime('%H:%M:%S.%f')
            self.signals.nextStep.emit(f'This took: {deltaT}')
        

#currently this is just for uploading 1 job to cloud
#this is a worker so that life is easier for ui and so that status updates get thrown back as signals
class cloudTransferWorker(QRunnable):
    def __init__(self, signals, sessionDict, mouseID, source):
        super().__init__()
        self.signals = signals
        self.sessionDict = sessionDict
        self.mouseID = mouseID
    def run(self):
        self.signals.nextStep.emit('Sending Data To The Cloud')
        source_dir = PurePosixPath(self.sessionDict['destination'])
        subject_id  = str(self.sessionDict['subject_id'])
        acq_datetime = self.sessionDict['acquisition_datetime']
        platform = Platform.BEHAVIOR
        behavior_config = ModalityConfigs(modality=Modality.BEHAVIOR, source=(source_dir / "Behavior"))
        behavior_videos_config = ModalityConfigs(modality=Modality.BEHAVIOR_VIDEOS, source=(source_dir / "Behavior videos"))
        project_name  = self.sessionDict['project_name']
        metadata_dir = self.sessionDict['destination'] #I think this is what it means for metadata dir..
        s3_bucket = self.sessionDict['s3_bucket']
        upload_job_configs = BasicUploadJobConfigs(
          project_name=project_name,
          s3_bucket=s3_bucket,
          platform=platform,
          subject_id=subject_id,
          acq_datetime=acq_datetime,
          modalities=[behavior_config, behavior_videos_config],
          metadata_dir=metadata_dir
        )
        upload_jobs = [upload_job_configs]
        #no need to email anyone for time being... but maybe make a secret dictionary that pairs emails with experimenters 
        #that way whoever uploads to cloud after experiment, it can 
        # user_email = "my_email_address"
        # email_notification_types = ["fail"]
        # submit_request = SubmitJobRequest(
        #   upload_jobs=upload_jobs,
        #   user_email=user_email,
        #   email_notification_types=email_notification_types,
        # )
        post_request_content = json.loads(submit_request.model_dump_json(round_trip=True, exclude_none=True))
        # Uncomment the following to submit the request
        # submit_job_response = requests.post(url="http://aind-data-transfer-service/api/v1/submit_jobs", json=post_request_content)
        # print(submit_job_response.status_code)
        # print(submit_job_response.json())
        
        self.signals.stepComplete.emit('Data successfully uploaded to cloud!')
        

        
# class sleeperScatchTransfer(QRunnable):
#     def __init(self, signals, paramDict):
#         super().__init__()
#         self.signals = signals
#         self.paramDict = paramDict
#     def run(self):
#         print('Will run this at midnight, transfer all data to vast (no cloud uploads, cloud jobs done manually for now until something cool can be determined')
        