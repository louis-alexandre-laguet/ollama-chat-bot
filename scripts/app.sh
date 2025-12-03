#!/bin/bash

# ========================================
# Script to manage application services
# ========================================

# Define variables
COMPOSE_FILE="../podman/app.docker-compose.yaml"
CONTAINER_NAME="app-container"

# Check if a command-line parameter is provided
if [ -z "$1" ]; then
    echo "[ Error ] No parameter provided. Usage: $0 [start|restart|stop|remove]"
    exit 1
fi

# Handle different commands based on the provided parameter
case "$1" in
    start)
        # Start services defined in the Docker Compose file
        echo "[ Starting services ]"
        podman compose -f "$COMPOSE_FILE" up -d

        # Continuously display the logs of the app container
        echo [ Displaying logs ]
        podman logs --follow "$CONTAINER_NAME"
        ;;
    restart)
        # Restart services by stopping and then starting them again
        echo "[ Restarting services ]"
        podman compose -f "$COMPOSE_FILE" down
        podman compose -f "$COMPOSE_FILE" up -d

        # Continuously display the logs of the app container
        echo [ Displaying logs ]
        podman logs --follow "$CONTAINER_NAME"
        ;;
    stop)
        # Stop all services defined in the Docker Compose file
        echo "[ Stopping services ]"
        podman compose -f "$COMPOSE_FILE" down
        ;;
    remove)
        # Stop all services
        echo "[ Removing services ]"
        podman compose -f "$COMPOSE_FILE" down
        
        # Remove previously built Docker image
        echo "[ Removing Docker images ]"
        podman rmi localhost/app-image:latest
        ;;
    reset)
        # Stop all services
        echo "[ Removing services ]"
        podman compose -f "$COMPOSE_FILE" down
        
        # Remove previously built Docker image
        echo "[ Removing Docker images ]"
        podman rmi localhost/app-image:latest
        
        # Start services defined in the Docker Compose file
        echo "[ Starting services ]"
        podman compose -f "$COMPOSE_FILE" up -d

        # Continuously display the logs of the app container
        echo [ Displaying logs ]
        podman logs --follow "$CONTAINER_NAME"
        ;;
    *)
        # Handle invalid commands
        echo "[ Error ] Invalid parameter. Usage: $0 [start|restart|stop|remove]"
        exit 1
        ;;
esac
