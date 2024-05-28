@echo off

setlocal enabledelayedexpansion
set i=0
for /f "tokens=2 delims==" %%a in ('wmic path win32_VideoController get name /value') do (
    set /a i+=1
    set "GPU_NAME[!i!]=%%a"
)

set /p PYTHON_PATH="Inserisci la cartella di installazione di Python (3.11): "

for /f "tokens=2" %%i in ('%PYTHON_PATH%python --version') do set PYTHON_VERSION=%%i
for /f "tokens=1,2,3 delims=." %%j in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR_VERSION=%%j
    set PYTHON_MINOR_VERSION=%%k
    set PYTHON_PATCH_VERSION=%%l
)

if %PYTHON_MAJOR_VERSION%==2 (
    echo ^[[31m"Python 2.x is not supported. Please install Python 3.x."^[[0m
    echo ^[[33m"Please install Python 3.11 from https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"^[[0m
    pause
)

if %PYTHON_MAJOR_VERSION%==3 (
    if %PYTHON_MINOR_VERSION% LSS 11 (
        echo ^[[31m"Python 3.11 or higher is required. Please install Python 3.11.9 or higher."^[[0m
        echo ^[[33m"Please install Python 3.11.9 from https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"^[[0m
        pause
    )
)

%PYTHON_PATH%python -m venv ollamarag
echo ^[[32m"Virtual environment created successfully."^[[0m

call ollamarag\Scripts\activate
echo ^[[32m"Virtual environment activated successfully."^[[0m

python -m pip install --upgrade pip

pip install chromadb --no-cache-dir
echo ^[[32m"Chromadb installed successfully."^[[0m

pip install pillow --no-cache-dir
echo ^[[32m"Pillow installed successfully."^[[0m

pip install langchain langchain-community --no-cache-dir
echo ^[[32m"Langchain installed successfully."^[[0m

pip install vt-py --no-cache-dir
echo ^[[32m"VirusTotal installed successfully."^[[0m

pip install transformers --no-cache-dir
echo ^[[32m"Transformers installed successfully."^[[0m

pip install open-clip-torch --no-cache-dir
echo ^[[32m"Open-clip-torch installed successfully."^[[0m
