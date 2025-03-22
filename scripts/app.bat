@echo off

REM ========================================
REM Script to manage application services
REM ========================================

REM Define variables
set COMPOSE_FILE=..\podman\app.docker-compose.yaml
set CONTAINER_NAME=app-container

REM Check for a parameter
if "%1"=="" (
    REM No parameter provided, show usage message and exit
    echo [ Error ] No parameter provided. "Usage: %0 [start|restart|stop|remove]"
    exit /b 1
)

REM Handle different commands based on the provided parameter
if "%1"=="start" (
    REM Start services defined in the Docker Compose file
    echo [ Starting services ]
    podman-compose -f %COMPOSE_FILE% up -d

    REM Continuously display the logs of the app container
    echo [ Displaying logs ]
    podman logs --follow %CONTAINER_NAME%

) else if "%1"=="restart" (
    REM Restart services by stopping and then starting them again
    echo [ Restarting services ]
    podman-compose -f %COMPOSE_FILE% down
    podman-compose -f %COMPOSE_FILE% up -d

    REM Continuously display the logs of the app container
    echo [ Displaying logs ]
    podman logs --follow %CONTAINER_NAME%

) else if "%1"=="stop" (
    REM Stop all services defined in the Docker Compose file
    echo [ Stopping services ]
    podman-compose -f %COMPOSE_FILE% down

) else if "%1"=="remove" (
    REM Stop all services
    echo [ Removing services ]
    podman-compose -f %COMPOSE_FILE% down

    REM Remove previously built Docker image
    echo [ Removing Docker images ]
    podman rmi localhost/app-image:latest

) else if "%1"=="reset" (
    REM Stop all services
    echo [ Removing services ]
    podman-compose -f %COMPOSE_FILE% down

    REM Remove previously built Docker image
    echo [ Removing Docker images ]
    podman rmi localhost/app-image:latest

    REM Start services defined in the Docker Compose file
    echo [ Starting services ]
    podman-compose -f %COMPOSE_FILE% up -d

    REM Continuously display the logs of the app container
    echo [ Displaying logs ]
    podman logs --follow %CONTAINER_NAME%

) else (
    REM Handle invalid parameters
    echo [ Error ] Invalid parameter. "Usage: %0 [start|restart|stop|remove]"
    exit /b 1
)
