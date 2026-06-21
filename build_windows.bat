@echo off
REM build_windows.bat - Build .exe for FM Player Face Tool Pro
REM
REM Prerequisites:
REM   pip install pyinstaller
REM
REM Usage:
REM   build_windows.bat

echo === Building FM Player Face Tool Pro (.exe) ===
pyinstaller build.spec --distpath dist --workpath build\pyinstaller --noconfirm

echo.
echo === Done ===
echo Executable: dist\FMFaceTool.exe
pause
