@echo off
REM Load environment variables from .env file
for /f "usebackq tokens=1,2 delims==" %%i in (".env") do (
    if not "%%i"=="" if not "%%j"=="" (
        set "%%i=%%j"
        echo Setting %%i=%%j
    )
)

REM Ensure required ADK variables are set
if not defined GOOGLE_GENAI_USE_VERTEXAI (
    set GOOGLE_GENAI_USE_VERTEXAI=FALSE
    echo Setting GOOGLE_GENAI_USE_VERTEXAI=FALSE
)

REM Display current API key status (masked)
if defined GOOGLE_API_KEY (
    echo GOOGLE_API_KEY is set
) else (
    echo ERROR: GOOGLE_API_KEY is not set
    pause
    exit /b 1
)

REM Start ADK server
echo Starting ADK server...
adk api_server --host 0.0.0.0 --port 8000
