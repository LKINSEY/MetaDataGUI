# MetaDataGUI
This GUI organizes and creates AIND metadata for 2p imaging (scanimage) + behavior (pybpod) + videography (pyspincapture) experiments on our Bergamo 2p microscope.




Data is saved on VAST as follows: <br>
-- /allen/aind/scratch/BCI/2p-raw <br>
&nbsp;&nbsp; -- /mouseWRname<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;    --/date <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      --/behavior <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;     --/behaviorvideo <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      --/pophys <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      --/rig.json <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;      --/session.json <br>

# Installation
Go through all the steps.


## Install AIND metadata dependencies
```
conda create -n codeocean python=3.11
conda activate codeocean
pip install codeocean, aind_data_schema_models
pip install git+https://github.com/AllenNeuralDynamics/aind-data-transfer-service.git
```
maybe
#aind_data_transfer_models, aind_data_transfer_service

## Install Pybpod and scanimage dependencies
go somewhere you want these codes to be
```
git clone https://github.com/rozmar/suite2p.git
cd suite2p
conda env create -f environment.yml
conda activate bci_with_suite2p
pip install -e .
cd ..
git clone https://github.com/kpdaie/BCI_analysis.git
cd BCI_analysis
pip install -e .
```

## Open GUI
where you want gui to be located (and preferably in miniconda)
```
conda activate codeocean
git clone https://github.com/LKINSEY/MetaDataGUI.git
cd metaDataGUI\UI
python metaDataGUI_updateInProgress.py
```

##AIND USAGE ONLY
map: \\allen\aind\scratch\BCI\2p-raw to Y: drive


# Usage
![image](https://github.com/user-attachments/assets/348a11a1-eaf1-4a7d-ac49-e7906ec96fff)
