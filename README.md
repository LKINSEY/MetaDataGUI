# MetaDataGUI
This GUI organizes and creates AIND metadata for 2p imaging (scanimage) + behavior (pybpod) + videography (pyspincapture) experiments on our Bergamo 2p microscope.




Data is saved on VAST as follows: <br>

/allen/aind/scratch/BCI/2p-raw  
  └── /mouseWRname  
      └── /date  
          ├── /behavior  
          ├── /behaviorvideo  
          ├── /pophys  
          ├── /rig.json  
          └── /session.json  

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


## AIND metadata dependencies
- aind_data_transfer_models
- aind_data_schema_models
- aind_data_transfer_service


## Pybpod and scanimage dependencies
# Usage
![image](https://github.com/user-attachments/assets/348a11a1-eaf1-4a7d-ac49-e7906ec96fff)
