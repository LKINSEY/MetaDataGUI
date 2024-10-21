import os, time
from pathlib import Path
from datetime import datetime
import pandas as pd
import os,json, subprocess, shutil
import numpy as np
#from aind_data_schema.visualizations import plot_session
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib
from typing import List, Tuple
from datetime import datetime
import bergamo_rig
from aind_metadata_mapper.bergamo.session import ( BergamoEtl, 
                                                  JobSettings,
                                                  RawImageInfo,
                                                  )


#utilities
# =============================================================================
# def extract_behavior(mouse_name, session_folder,staging_dir):
#     command = ['export_behavior.bat',  mouse_name, session_folder,staging_dir]
#     print('-------------- \n Extracting Behavior... \n ------------------')
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
#     print('Sub process is working')
#     count = 0
#     while True:
#         time.sleep(10)
#         print(f'Still writing after {count}0 seconds...')
#         count += 1
#         if len(os.listdir(staging_dir))>0:
#             print('Behavior Files Created')
#             break
#     #     output = process.stdout.readline()
#     #     if output == '' and process.poll() is not None:
#     #         break
#     #     if output:
#     #         print(output.strip())
# 
#     # rc = process.poll()
#     # return rc
# =============================================================================



def extract_behavior(mouse_name, session_folder, staging_dir):
    command = ['export_behavior.bat', mouse_name, session_folder, staging_dir]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    stdout, stderr = process.communicate()

    if stdout:
        print("Output:\n", stdout)
    if stderr:
        print("Errors:\n", stderr)

    rc = process.returncode
    return rc



#METADATA FUNCTIONS


import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import json
import os
from typing import List, Tuple


from matplotlib.dates import DateFormatter
# import matplotlib.pyplot as plt
import matplotlib
font = {'family' : 'Sans',
        #'weight' : 'bold',
        'size'   : 18}
matplotlib.rc('font', **font)

def load_metadata_from_folder(folder: str, models: List[str] = None) -> dict:
    """Load metadata from a folder containing JSON files."""

    models = ["subject", "procedures", "session", "acquisition", "processing"] if models is None else models

    # identify what metadata is present
    md = {}
    for k in models:
        path = os.path.join(folder, f"{k}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                md[k] = json.load(f)

    return md
def plot_session(session: dict) -> Tuple[plt.Figure, plt.Axes]:
    """Creates a timeline of events during a session including Data Streams and Stimulus Epochs.

    Args:
        session (dict): dictionary containing session metadata
    """

    fig, ax = plt.subplots(figsize=(15, 8))
    for stream in session["data_streams"]:
        stream_start_time = datetime.fromisoformat(stream["stream_start_time"]).replace(tzinfo=None)
        stream_end_time = datetime.fromisoformat(stream["stream_end_time"]).replace(tzinfo=None)
        ax.hlines(
            1, mdates.date2num(stream_start_time), mdates.date2num(stream_end_time), linewidth=8, alpha=0.3, color="r"
        )
        s_text = ''
        for sm in stream['stream_modalities']:
            if stream['stack_parameters'] != None:
                s_text += sm['abbreviation'] + ' stack' + '\n'
            else:
                s_text += sm['abbreviation'] + '\n'
        ax.text(stream_start_time, 1.1, s_text, rotation=90, ha="left", va="bottom")
    #     ax.scatter(mdates.date2num(stream_start_time), [1], marker='|', color='blue', s=100)

    for epoch in session["stimulus_epochs"]:
        stimulus_start_time = datetime.fromisoformat(epoch["stimulus_start_time"]).replace(tzinfo=None)
        stimulus_end_time = datetime.fromisoformat(epoch["stimulus_end_time"]).replace(tzinfo=None)
        ax.hlines(2, mdates.date2num(stimulus_start_time), mdates.date2num(stimulus_end_time), linewidth=8, alpha=0.3)
        #     ax.scatter(mdates.date2num(stimulus_start_time), [2], marker='|', color='red', s=100)
        ax.text(stimulus_start_time, 2.1, epoch["stimulus_name"]+ '\n' + epoch['output_parameters']['tiff_stem'], rotation=90, ha="center", va="bottom")

    ax.xaxis.set_major_locator(mdates.HourLocator())
    loc = mdates.MinuteLocator(byminute=[0, 15, 30, 45])
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(loc))
    ax.set_yticks([1, 2])
    ax.set_yticklabels(["Streams", "Stimuli"])

    plt.tight_layout()

    return fig, ax


#plot

def plot_behavior(bpod_data,mouse_name,session_date):
    scanimage_file_names = list()
    basenames = list()
    file_indices = list()
    trial_indices = list()
    for trial_i,sfn in enumerate(bpod_data['scanimage_file_names']):
        if type(sfn) == type('no movie for this trial'):
            continue
        else:
            for file in sfn:
                if '_' in file:# and ('cell' in file.lower() or 'stim' in file.lower()):
                    basenames.append(file[:-1*file[::-1].find('_')-1])
                    try:
                        file_indices.append(int(file[-1*file[::-1].find('_'):file.find('.')]))
                    except:
                        print('weird file index: {}'.format(file))
                        file_indices.append(-1)
                else:
                    basenames.append(file[:file.find('.')])
                    file_indices.append(-1)
                trial_indices.append(trial_i)
                scanimage_file_names.append(file)
    
                
    scanimage_file_names = np.asarray(scanimage_file_names)
    basenames =np.asarray(basenames)
    file_indices =np.asarray(file_indices)
    trial_indices = np.asarray(trial_indices)
    
    unique_basenames = np.unique(basenames)
    basenames_order = []
    for basename in unique_basenames:
        basenames_order.append(np.argmax(np.asarray(basenames)==basename))
    unique_basenames = unique_basenames[np.argsort(basenames_order)]
    
    
    fig = plt.figure(figsize = [15,15])
    ax = fig.add_subplot(1,1,1)
    fig2 = plt.figure(figsize = [15,7])
    ax_time_to_hit = fig2.add_subplot(1,1,1)
    ax_hit = ax_time_to_hit.twinx()
    trials_so_far = 1
    basenames_plotted = []
    time_to_threshold_crossing = []
    time_to_lick = []
    for basename in unique_basenames:
        trials_now = basename==basenames
        trial_indices_now = trial_indices[trials_now]
        hits = []
        trial_indices_to_plot = []
        time_to_threshold_crossing = []
        time_to_lick = []
        for trial_i,trial_idx in enumerate(trial_indices_now):
            go_cue_time = bpod_data['go_cue_times'][trial_idx][0]
            scanimage_trigger_time =bpod_data['Scanimage_trigger_times'][trial_idx][0]
            lick_times =bpod_data['lick_L'][trial_idx]
            reward_times =bpod_data['reward_L'][trial_idx]
            lickport_step_times =bpod_data['zaber_move_forward'][trial_idx]
            threshold_crossing_time = bpod_data['threshold_crossing_times'][trial_idx]
            if len(threshold_crossing_time)>0:
                lickport_step_times = lickport_step_times[lickport_step_times<=threshold_crossing_time[0]]
                time_to_threshold_crossing.append(threshold_crossing_time[0])
            else:
                time_to_threshold_crossing.append(np.nan)
            
            zero_time = go_cue_time
            
            ax.plot(lick_times-zero_time,np.ones(len(lick_times))*(trial_i+trials_so_far),'b.')
            if len(reward_times)>0:
                ax.plot(reward_times[0]-zero_time,trial_i+trials_so_far,'ro')
                hits.append(1)
                time_to_lick.append(reward_times[0]-threshold_crossing_time[0])
            else:
                ax.plot(10,trial_i+trials_so_far,'ko')
                hits.append(0)
                time_to_lick.append(np.nan)
            trial_indices_to_plot.append(trial_i+trials_so_far)
            ax.plot(lickport_step_times-zero_time,np.ones(len(lickport_step_times))*(trial_i+trials_so_far),'k|')
        trials_so_far += trial_i + 1
        basenames_plotted.append(basename)
        
        ax.hlines(trials_so_far+.5,0,20,color= 'blue',linestyles = 'dashed')
        
        hit_rate = np.convolve(hits,np.ones(10)/10,mode = 'same')
        hit_rate[:5] = np.nan
        hit_rate[-5:] = np.nan
        if len(trial_indices_to_plot)>10:
            ax_hit.plot(trial_indices_to_plot,hit_rate,'k-')
        ax_hit.vlines(trials_so_far+.5,0,1,color= 'blue',linestyles = 'dashed')
        ax_time_to_hit.plot(trial_indices_to_plot,time_to_threshold_crossing,'g.')
        #ax_time_to_hit.plot(trial_indices_to_plot,time_to_lick,'r.')
    ax_time_to_hit.set_yscale('log')
        
    ax_time_to_hit.set_ylabel('')
    ax.set_ylim([trials_so_far+1,0])
    ax.set_xlim([-.5, 10.5])
    ax.set_xlabel('Time from GO cue')
    ax.set_ylabel('Trial #')
    title_ = ''
    for bni,bn in enumerate(basenames_plotted):
        if bni>0:
            title_ = title_+ ' -- '
        title_ = title_+ bn
    ax.set_title(title_)
    
    ax_time_to_hit.set_ylabel('Time to hit (s)') # / lick
    ax_time_to_hit.set_xlabel('Trial#')
    ax_time_to_hit.set_title('{} - {}'.format(mouse_name,session_date))
    ax_hit.set_ylabel('Hit rate')

    return [fig,fig2]




#Generate JSONS

#Session JSON
def prepareSessionJSON(behavior_folder_staging, behavior_fname):
    #inputs == behavior_folder_staging, behavior_fname, 
    #define an error message

    # create session json from bpod dict, tiff folder and user input
    behavior_data = np.load(os.path.join(behavior_folder_staging,behavior_fname),allow_pickle = True).tolist()
    bpod_file_names = np.unique(behavior_data['bpod_file_names'])    
    command_list = []
    #likely if but, it will be here...
    for f in bpod_file_names:
        shutil.copyfile(f, behavior_folder_staging.joinpath(Path(f).name))
    goodtrials = []
    hittrials = []
    #going to assume if no behavior videos recorded, all trials are good...? is this a safe assumption?
    if len(behavior_data['scanimage_file_names'])==20:#if == 'no movie files found'
        goodtrials = np.full((1,len(behavior_data['reward_L'])), True)
        hittrials = np.where((behavior_data['reward_L'])>0, True, False)
    else:    
        for r,sfn in zip(behavior_data['reward_L'],behavior_data['scanimage_file_names']):
            if type(sfn) == str:
                goodtrials.append(False)
            else:
                goodtrials.append(True)
            if len(r)==0:
                hittrials.append(False)
            else:
                hittrials.append(True)
    goodtrials = np.asarray(goodtrials)    
    hittrials = np.asarray(hittrials)    
    is_side_camera_active = False
    is_bottom_camera_active = False
    for movienames in behavior_data['behavior_movie_name_list'][goodtrials]:
        for moviename in movienames:
            if 'side' in moviename:
                is_side_camera_active = True
            if 'bottom' in moviename:
                is_bottom_camera_active = True
            if is_bottom_camera_active and is_side_camera_active:
                break
        if is_bottom_camera_active and is_side_camera_active:
                break
    cn_num = []
    for cn_now in behavior_data['scanimage_roi_outputChannelsRoiNames']:
        cn_num.append(len(cn_now))
    cn_num = int(np.mean(np.asarray(cn_num)[goodtrials]))
    if cn_num ==1:
        behavior_task_name = "single neuron BCI conditioning"
    elif cn_num ==2:
        behavior_task_name = "two neuron BCI conditioning"
    elif cn_num>2:
        behavior_task_name = "multi-neuron BCI conditioning"
    else:
        return 
    print(behavior_task_name)
    return behavior_data, hittrials, goodtrials, behavior_task_name, is_side_camera_active, is_bottom_camera_active


def stagingVideos(behavior_data, behavior_video_folder_staging):
    original_movie_basefolder = Path('//10.128.54.109/Data/Behavior_videos')
    side_folders = []
    bottom_folders = []
    for m in behavior_data['behavior_movie_name_list']:
        if type(m) == np.ndarray:
            for movie_name in m:
                if 'side' in movie_name:
                    side_folders.append(original_movie_basefolder.joinpath(Path(*movie_name.split('/')[5:-1])))
                elif 'bottom' in movie_name:
                    bottom_folders.append(original_movie_basefolder.joinpath(Path(*movie_name.split('/')[5:-1])))
                else:
                    return 
                    # err = QErrorMessage(self)
                    # err.showMessage('No Videos! - Aborting Processing Pipeline -- YAML not made')
                    # err.exec()
    side_folders = np.unique(side_folders)
    bottom_folders = np.unique(bottom_folders)
    behavior_video_folders = ''
    if len(side_folders)>0:
        side_dest_folder = Path(behavior_video_folder_staging).joinpath(Path('side'))#
        side_dest_folder.mkdir(parents=True, exist_ok=True)
        for side_folder in side_folders:
            shutil.copytree(side_folder, side_dest_folder.joinpath(Path(side_folder).name), dirs_exist_ok=True)
        if len(behavior_video_folders)==0:
            behavior_video_folders = str(behavior_video_folder_staging )

    if len(bottom_folders)>0:
        bottom_dest_folder = Path(behavior_video_folder_staging).joinpath(Path('bottom'))#
        bottom_dest_folder.mkdir(parents=True, exist_ok=True)
        for bottom_folder in bottom_folders:
            shutil.copytree(bottom_folder, bottom_dest_folder.joinpath(Path(bottom_folder).name), dirs_exist_ok=True)
        if len(behavior_video_folders)==0:
            behavior_video_folders = str(behavior_video_folder_staging )
    mpeg_files_side = []
    mpeg_files_bottom = []
    for behavior_video_folder in os.listdir(behavior_video_folders):
        behavior_video_folder = os.path.join(behavior_video_folders,behavior_video_folder)
        for behavior_video_subfolder in os.listdir(behavior_video_folder):
            for file in os.listdir(Path(behavior_video_folder).joinpath(Path(behavior_video_subfolder))):
                if '.mp4' in file:
                    if 'bottom' in behavior_video_folder:
                        mpeg_files_bottom.append(file)
                    elif 'side' in behavior_video_folder:
                        mpeg_files_side.append(file)
    print('{} side camera videos and {} bottom camera videos staged'.format(len(mpeg_files_side),len(mpeg_files_bottom)))


def createPDFs(staging_dir, behavior_data, mouseID, date):
    from matplotlib.backends.backend_pdf import PdfPages

    md = load_metadata_from_folder(staging_dir)#Path(staging_dir).joinpath(Path('session.json'))
    fig,ax = plot_session(md['session'])
    
    md['session']['session_start_time']
    [fig2,fig3] = plot_behavior(behavior_data, mouseID,date)
    pdf_obj = PdfPages(Path(staging_dir).joinpath(Path('session_plots.pdf')))
    pdf_obj.savefig(fig) 
    pdf_obj.savefig(fig2)
    pdf_obj.savefig(fig3)
    pdf_obj.close()


































