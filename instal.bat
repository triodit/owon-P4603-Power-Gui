@echo off
echo Installing Python dependencies...

REM Install pip if not already installed
python -m ensurepip --default-pip

REM Install required packages using pip
pip install tkinter
pip install serial 
pip install pyserial 
pip install matplotlib

if %errorlevel% neq 0 (
    echo There was an error during installation. Please check the output above.
) else (
    echo.
    echo All dependencies have been successfully installed!
)

echo.
echo Installation complete. Press any key to exit.
pause >nul