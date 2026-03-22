@echo off

SET ENV_FILE=.env

FOR /F "usebackq tokens=*" %%i IN ("%ENV_FILE%") DO (
    REM Skip empty lines and lines starting with REM
    IF NOT "%%i"=="" IF NOT "%%i"=="REM" (
        REM Check if the line starts with # (for comments)
        FOR /F "tokens=1* delims=#" %%j IN ("%%i") DO (
            REM Set the environment variable
            SET %%j
        )
    )
)

venv\scripts\python.exe -m build
venv\scripts\python.exe -m twine upload dist/*