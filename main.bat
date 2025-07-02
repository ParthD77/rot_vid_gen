

echo Running video_process.py...
python video_process.py
if %errorlevel% neq 0 (
    echo script1.py FAILED with error code %errorlevel%
    pause
    exit /b %errorlevel%
)
echo video_process.py completed successfully.

echo Running cleanup.py...
python cleanup.py
if %errorlevel% neq 0 (
    echo script2.py FAILED with error code %errorlevel%
    pause
    exit /b %errorlevel%
)
echo cleanup.py completed successfully.

pause