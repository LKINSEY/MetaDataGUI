@ECHO OFF
call conda activate codeocean
set folderPath = %~dp0UI
if exist "%UI%" (
	echo Navigating to %folderPath%
	cd "%folderPath%"
	python metaDataGUI_workInProgress.py
)

pause