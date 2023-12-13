@echo off

SET file=Chloe_fr_FR.pro
SET tsfile=Chloe_fr_FR.ts
SET PYTHONHOME=C:\Program Files\QGIS 3.28.4\apps\Python39
SET PYTHONPATH=C:\Program Files\QGIS 3.28.4\apps\Python39\lib
echo Construction du fichier %file%...
echo SOURCES = \ > %file%
for /r .. %%X in (*.py) do call echo    %%X \ >> %file%
echo    fake.py >> %file%   
echo FORMS = \ >> %file%
for /r .. %%X in (*.ui) do call echo    %%X \ >> %file%   
echo    fake.ui >> %file%   
echo TRANSLATIONS = %tsfile% >> %file%
echo OK
REM for /r .. %%X in (*.ts) do call echo    %%X \ >> %file%   
REM for /r .. %%X in (*.py) do call set "list=%%list%% \ \n %%X";   
echo Mise a jour du fichier %tsfile%...
REM type %file%
"C:\Program Files\QGIS 3.28.4\apps\Python39\Scripts\pylupdate5.exe" -noobsolete %file%
echo OK

