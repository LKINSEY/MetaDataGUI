@ECHO OFF
call conda activate codeocean2
set folderPath=%~dp0UI
echo "%folderPath%"
if exist "%folderPath%" (
	echo Navigating to %folderPath%
	cd %folderPath%
	python metaDataGUI_updateInProgress.py

) else (
	echo Does not exist "%folderPath% "
)

