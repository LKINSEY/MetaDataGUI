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
pip install codeocean, aind_data_transfer_models, aind_data_transfer_service, aind_data_schema_models
```

## Install Pybpod and scanimage dependencies
```
conda create --name bci_analysis python=3.8 -y
conda activate bci_analysis
git clone https://github.com/kpdaie/BCI_analysis.git
cd BCI_analysis
pip install -e .
```


# Usage
![image](https://github.com/user-attachments/assets/348a11a1-eaf1-4a7d-ac49-e7906ec96fff)
