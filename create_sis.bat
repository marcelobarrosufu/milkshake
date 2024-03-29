REM 
REM DO NOT TRY TO GENERATE THE SIS FILE IF YOUR PATH CONTAINS SPACES.
REM ENSYMBLE DOES NOT SUPPORT THEM ! COPY THIS PROJECT TO C:\
REM BEFORE RUNNING THIS SCRIPT.
REM
@echo off

IF "%1" EQU "" GOTO error

SET PYTHON=C:\Python25\python.exe
SET APPNAME=Milkshake
SET CAPBLS=NetworkServices+LocalServices+ReadUserData+WriteUserData+UserEnvironment
SET SRCDIR=src
SET TMPDIR=src.tmp
SET ICON=img\none.svg

REM put you zip tool here
SET ZIP="C:\Arquivos de programas\7-Zip\7z.exe"
REM Path to module-repo, inside Python For S60
SET PYS60DIR=C:\Arquivos de programas\PythonForS60

SET OPTS=--verbose --version="%1" --appname="%APPNAME%" ^
         --extrasdir=extras --heapsize=4k,5M --caps=%CAPBLS% --icon="%ICON%"

REM --icon="%ICON%"
echo "Populating temp dir"
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
mkdir %TMPDIR%\extras\data\python\milkshakedir\plugins

copy  %SRCDIR%\lib\               %TMPDIR%\extras\data\python\milkshakedir\
xcopy /S %SRCDIR%\plugins         %TMPDIR%\extras\data\python\milkshakedir\plugins\
copy  %SRCDIR%\lib\milkshake.mif  %TMPDIR%\extras\data\python\milkshakedir
copy  %SRCDIR%\default.py         %TMPDIR%\

if not exist .\module-repo\ xcopy /E "%PYS60DIR%\module-repo" .\module-repo\
if not exist .\templates\   xcopy /E "%PYS60DIR%\templates"   .\templates\
if not exist ensymble.py    xcopy /E "%PYS60DIR%\ensymble.py" .
if not exist openssl.exe    xcopy /E "%PYS60DIR%\openssl.exe" .

%PYTHON% ensymble.py py2sis %OPTS% "%TMPDIR%" "%APPNAME%-%1.sis"

echo "Zipping source files"
%ZIP% a -r -tzip %APPNAME%-%1-src.zip src

goto end

:error
echo Sintaxe: %0 version

:end


