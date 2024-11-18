from PyQt6.QtCore import QRunnable, pyqtSignal, QObject, QThreadPool
import traceback, os, json, traceback, shutil, requests
from pathlib import Path, PurePosixPath
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date
from aind_metadata_mapper.bergamo.session import ( BergamoEtl, 
                                                  JobSettings,
                                                  )
import bergamo_rig
from typing import Optional
from aind_data_transfer_models.core import (
    ModalityConfigs,
    BasicUploadJobConfigs,
    SubmitJobRequest,
)
from aind_data_schema_models.modalities import Modality
from aind_data_schema_models.platforms import Platform
from main_utility import *


class WorkerSignals(QObject):
    startingTransfer = pyqtSignal()
    transferingSignal = pyqtSignal(str)
    dataOnScratch = pyqtSignal(str)
    processingStep = pyqtSignal(str)
    error = pyqtSignal(str)
    cloudTransfer = pyqtSignal()

 


class metaDataWorker(QRunnable):
    def __init__(self, signals, paramDict, whatToProcess):
        super().__init__()
        self.signals = signals
        self.params = paramDict
        self.sessionData = {}
        self.mouseDict = {}
        self.processBool = whatToProcess #[behavior, behavior_videos, pophys]
    
    def run(self):


        ############################ TRANSFER TO SCRATCH FIRST ################################
        
        #Load Init JSON and mouseDict JSON and establish data paths
        localPath = self.params.get('localPath')
        scratchPath = self.params.get('pathToRawData')
        WRname = self.params.get('WRname')
        dateEnteredAs = self.params.get('date')
        try:
            dateTimeObj = datetime.strptime(dateEnteredAs,'%Y-%m-%d').date()
            dateFileFormat = dateTimeObj.strftime('%m%d%y') #mmddyy
        except ValueError:
            dateFileFormat = str(dateEnteredAs) #already entered as mmddyy
        sourceDir = localPath+f'/{WRname}/{dateFileFormat}'
        destinationDir = scratchPath+f'/{WRname}/{dateFileFormat}/pophys'
        
        if not os.path.exists(destinationDir):
            shutil.copytree(sourceDir, destinationDir, copy_function=self.verboseCopy)
            self.signals.dataOnScratch.emit('Done Copying!')
            for i in range(1, 3):  # Let 3 seconds go by so someone can see this message
                QThreadPool.globalInstance().waitForDone(1000)  
        else:
            self.signals.dataOnScratch.emit('Data already on scratch!')
            for i in range(1, 3):  # Let 3 seconds go by so someone can see this message
                QThreadPool.globalInstance().waitForDone(1000) 
        
        #########################################################################################

        #starting processing behavior
        self.signals.processingStep.emit('Processing Behavior')
        try:
            dateTimeObj = datetime.strptime(dateEnteredAs,'%Y-%m-%d').date()
            dateFileFormat = dateTimeObj.strftime('%m%d%y') #mmddyy]
        except ValueError:
            dateFileFormat = str(dateEnteredAs) #already entered as mmddyy
        
        #I want the staging directory to be the scratch location, saved in mouse-->date-->data format, then in the mouse/date/ file, we can have actual behavior data
        stagingDir = 'Y:/'  #self.params.get('stagingDir') #will contain the init.json and mouseDict.json
        sessionFolder = Path(self.params.get('pathToRawData') + f'/{WRname}/{dateFileFormat}') #Y:/BCI93/101724

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
            print('This mouse exists')
        else:
            self.mouseDict[WRname] = self.params.get('subjectID')
            with open(Path(stagingDir + '/mouseDict.json'), 'w') as f:
                json.dump(self.mouseDict, f)
        
        #Step 2: check if sessionFolder exists

        stagingMouseSessionPath = f'Y:/{WRname}/{dateFileFormat}/'#turned into scratch location             #Path(stagingDir).joinpath( Path(f'{WRname}_{dateEnteredAs}'))
        rawDataPath = f'Y:/{WRname}/{dateFileFormat}/pophys'

        if self.processBool[0] == 1:
            self.signals.processingStep.emit('Processing Behavior - Process Bpod')
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

                rc = extract_behavior(WRname, rawDataPath, behavior_folder_staging)

                behavior_fname = f"{Path(sessionFolder).name}-bpod_zaber.npy"
                self.signals.stepComplete.emit('Behavior Data Extracted Successfully')
            except Exception:
                self.signals.error.emit('Error extracting behavior -- check traceback -- aborting process')
                traceback.print_exc() 
                return        
        else:
            self.signals.processingStep.emit('Skipping Bpod processing')

        #Step 5: Generate Rig JSON
        try:
            self.signals.processingStep.emit('Generating Rig Json')
            rig_json = bergamo_rig.generate_rig_json()
            with open(Path(stagingMouseSessionPath).joinpath(Path('rig.json')), 'w') as json_file:
                json_file.write(rig_json)
        except Exception:
            self.signals.error.emit('Error generating rig json -- check traceback -- aborting process')
            traceback.print_exc() 
            return
        
        #Step 6: Generate Session JSON
        try:
            self.signals.processingStep.emit('Generating Session Json')
            self.signals.nextStep.emit('Generating Session JSON')
            scratchInput = Path(self.params.get('pathToRawData') + f'/{WRname}/{dateFileFormat}/pophys')
            behavior_data, hittrials, goodtrials, behavior_task_name, is_side_camera_active, is_bottom_camera_active,starting_lickport_position = prepareSessionJSON(behavior_folder_staging, behavior_fname)
            user_settings = JobSettings(    input_source                = Path(scratchInput), #date folder local i.e. Y:/BCI93/101724/pophys
                                            output_directory            = Path(stagingMouseSessionPath), #staging dir folder scratch  i.e. Y:/BCI93/101724
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
                                            starting_lickport_position  = starting_lickport_position,
                                            behavior_task_name          = behavior_task_name,
                                            hit_rate_trials_0_10        = np.nanmean(hittrials[goodtrials][:10]),
                                            hit_rate_trials_20_40       = np.nanmean(hittrials[goodtrials][20:40]),
                                            total_hits                  = sum(hittrials[goodtrials]),
                                            average_hit_rate            = sum(hittrials[goodtrials])/sum(goodtrials),
                                            trial_num                   = sum(goodtrials))
            etl_job = BergamoEtl(job_settings=user_settings,)
            session_metadata = etl_job.run_job()
        except Exception:
            self.signals.error.emit('Error generating session json -- check traceback -- aborting process')
            traceback.print_exc() 
            return
        #Step 7: Stage Videos (if chosen)
        if self.processBool[1] == 1:
            try:
                self.signals.processingStep.emit('Staging Videos')
                stagingVideos(behavior_data, behavior_video_folder_staging)
            except Exception:
                self.signals.error.emit('Error Staging Videos -- check traceback -- aborting process')
                traceback.print_exc() 
                pass
        else:
            self.signals.processingStep.emit('Skipping Videos')

        #Step 8: Create and display PDFs
        try:
            self.signals.processingStep.emit('Plotting...')
            createPDFs(stagingMouseSessionPath, behavior_data, str(self.sessionData['subject_id']), dateEnteredAs)
        except Exception:
            self.signals.error.emit('Error Generating PDFs -- check traceback -- aborting process')
            traceback.print_exc() 
            return

        #Complete!
        self.signals.processingStep.emit('DONE!')
        return
    
    def verboseCopy(self, src, dest):
        fileBeingCopied = src.split('/')[-1]
        filesInSrc = len(os.listdir(src))
        filesInDest = len(os.listdir(dest))
        self.signals.transferingSignal.emit(f'{fileBeingCopied} {filesInDest}/{filesInSrc}')
        return shutil.copy2(src,dest) 

#currently this is just for uploading 1 job to cloud
class cloudTransferWorker(QRunnable):
    def __init__(self, signals, params):
        super().__init__()
        self.signals = signals
        self.params = params


    def run(self):
        thisMouse = self.params.get('WRname')
        dateEnteredAs = self.params.get('date')
        subject_id = self.params['subjectID']
        service_url = "http://aind-data-transfer-service/api/v1/submit_jobs" # For testing purposes, use dev url
        project_name = "Brain Computer Interface"
        s3_bucket = "private"
        platform = Platform.SINGLE_PLANE_OPHYS
        # acquisition_datetime = datetime.fromisoformat("2024-10-23T15:30:39")#find correct way to state the acq_datetime
        codeocean_pipeline_id = "a2c94161-7183-46ea-8b70-79b82bb77dc0"
        codeocean_pipeline_mount: Optional[str] = "ophys"

        #adding codeocean capsule ID and mount
        pophys_config = ModalityConfigs(
            modality=Modality.POPHYS,
            source=(f"/allen/aind/scratch/BCI/2p-raw/{thisMouse}/{dateEnteredAs}/pophys"),
        )
        behavior_video_config = ModalityConfigs(
            modality=Modality.BEHAVIOR_VIDEOS,
            compress_raw_data=False,
            source=(f"/allen/aind/scratch/BCI/2p-raw/{thisMouse}/{dateEnteredAs}/behavior_video"),
        )
        behavior_config = ModalityConfigs(
            modality=Modality.BEHAVIOR,
            source=(f"/allen/aind/scratch/BCI/2p-raw/{thisMouse}/{dateEnteredAs}/behavior"),
        )
        
        upload_job_configs = BasicUploadJobConfigs(
            s3_bucket=s3_bucket,
            platform=platform,
            subject_id=subject_id,
            acq_datetime=self.params['session_end_time'],#acquisition_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            modalities=[pophys_config, behavior_config, behavior_video_config],
            metadata_dir=PurePosixPath(f"/allen/aind/scratch/BCI/2p-raw/{thisMouse}/{dateEnteredAs}"),
            process_capsule_id=codeocean_pipeline_id,
            project_name=project_name,
            input_data_mount=codeocean_pipeline_mount,
            force_cloud_sync=False,
        )

        upload_jobs = [upload_job_configs]
        submit_request = SubmitJobRequest(upload_jobs=upload_jobs)
        post_request_content = json.loads(submit_request.model_dump_json(exclude_none=True))
        #Submit request
        submit_job_response = requests.post(url=service_url, json=post_request_content)
        # print(submit_job_response.status_code)
        # print(submit_job_response.json())
        # self.signals.nextStep.emit('Data Sent!')
        

        
