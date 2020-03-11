@ECHO OFF
SET CURRENT_DIR=%~dp0
CD /D %CURRENT_DIR%
set file_name=%1.task
IF NOT EXIST %file_name% echo.>%file_name%
exit
