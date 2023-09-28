@echo off
call "C:\Program Files\QGIS 3.28.4\bin\o4w_env.bat"
call "C:\Program Files\QGIS 3.28.4\bin\python-qgis-ltr.bat"

@echo on
pyrcc5 -o resources.py resources.qrc

pause