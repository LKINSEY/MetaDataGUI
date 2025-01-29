#import argparse
import BCI_analysis
from pathlib import Path
import sys, os
#print(sys.argv)
#command = sys.argv[1]
args = sys.argv[1:]
print(args)
subject_names = [args[0]] #mouseName
calcium_imaging_raw_session_dir = Path(args[1]) #date folder that has raw data
save_dir = Path(args[2])
# print('bla bla bla')



raw_behavior_dirs = [Path('//10.128.54.244/Documents/Pybpod/BCI'),
                    Path('//10.128.54.244/Documents/Pybpod/BCI_obsolete/BCI'),
                    Path('//10.128.54.244/Documents/Pybpod/BCI_obsolete_2/BCI')]



zaber_root_folder = Path('//10.128.54.244/Documents/BCI_Zaber_data')

BCI_analysis.pipeline_bpod.export_single_pybpod_session(session =Path(str(calcium_imaging_raw_session_dir)[:-6]).name,
                                                         subject_names = subject_names,
                                                         save_dir= save_dir,
                                                         calcium_imaging_raw_session_dir = calcium_imaging_raw_session_dir,
                                                         raw_behavior_dirs = raw_behavior_dirs,
                                                         zaber_root_folder = zaber_root_folder)
