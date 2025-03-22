@echo off

REM ========================================
REM Script to manage Ollama services
REM ========================================

REM Define variables
set COMPOSE_FILE=..\podman\ollama.docker-compose.yaml
set CONTAINER_NAME=ollama-container

REM Check for a parameter
if "%1" == "" (
    echo [ Error ] No parameter provided. "Usage: %0 [start|restart|stop|remove] [model_name]"
    echo You can specify an optional model name when using the 'start' command. If no model is specified, 'llama3.2' will be used by default.
    echo To see the list of available models, visit https://ollama.com/library.
    exit /b 1
)

REM Handle different commands based on the parameter
if "%1" == "start" (
    REM Start services defined in the Docker Compose file
    echo [ Starting services ]
    podman-compose -f %COMPOSE_FILE% up -d

    REM Check for a model parameter
    if "%2" == "" (
        REM Run the llama3.2:3B model into the Ollama container
        echo [ Running llama3.2:3B ]
        podman exec %CONTAINER_NAME% ollama run llama3.2
    ) else (
        REM Run the specified model into the Ollama container
        echo [ Running %2 ]
        podman exec %CONTAINER_NAME% ollama run %2
        if errorlevel 1 (
            echo [ Error ] Failed to run the model '%2'.
            echo Please ensure the model name is correct. Visit https://ollama.com/library for available models.
            exit /b 1
        )
    )
) else if "%1" == "restart" (
    REM Restart services by stopping and then starting them again
    echo [ Restarting services ]
    podman-compose -f %COMPOSE_FILE% down
    podman-compose -f %COMPOSE_FILE% up -d
) else if "%1" == "stop" (
    REM Stop all services defined in the Docker Compose file
    echo [ Stopping services ]
    podman-compose -f %COMPOSE_FILE% down
) else if "%1" == "remove" (
    REM Stop all services and remove associated volumes
    echo [ Removing services and volumes ]
    podman-compose -f %COMPOSE_FILE% down -v
) else (
    REM Handle invalid parameters
    echo [ Error ] Invalid parameter. "Usage: %0 [start|restart|stop|remove] [model_name]"
    echo You can specify an optional model name when using the 'start' command. If no model is specified, 'llama3.2' will be used by default.
    echo To see the list of available models, visit https://ollama.com/library.
    exit /b 1
)
