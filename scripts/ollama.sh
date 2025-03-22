#!/bin/bash

# ========================================
# Script to manage Ollama services
# ========================================

# Define variables
COMPOSE_FILE="../podman/ollama.docker-compose.yaml"
CONTAINER_NAME="ollama-container"

# Check if a command-line parameter is provided
if [ -z "$1" ]; then
    echo "[ Error ] No parameter provided. Usage: $0 [start|restart|stop|remove] [model_name]"
    echo "You can specify an optional model name when using the 'start' command. If no model is specified, 'llama3.2' will be used by default."
    echo "To see the list of available models, visit https://ollama.com/library."
    exit 1
fi

# Handle different commands based on the provided parameter
case "$1" in
    start)
        # Start services defined in the Docker Compose file
        echo "[ Starting services ]"
        podman-compose -f "$COMPOSE_FILE" up -d

        # Check if a model name is provided
        if [ -z "$2" ]; then
            # Run the default llama3.2:3B model
            echo "[ Running llama3.2:3B ]"
            podman exec "$CONTAINER_NAME" ollama run llama3.2
            if [ $? -ne 0 ]; then
                echo "[ Error ] Failed to run the default model 'llama3.2'."
                exit 1
            fi
        else
            # Run the specified model
            echo "[ Running $2 ]"
            podman exec "$CONTAINER_NAME" ollama run "$2"
            if [ $? -ne 0 ]; then
                echo "[ Error ] Failed to run the model '$2'."
                echo "Please ensure the model name is correct. Visit https://ollama.com/library for available models."
                exit 1
            fi
        fi
        ;;
    restart)
        # Restart services by stopping and then starting them again
        echo "[ Restarting services ]"
        podman-compose -f "$COMPOSE_FILE" down
        podman-compose -f "$COMPOSE_FILE" up -d
        ;;
    stop)
        # Stop all services defined in the Docker Compose file
        echo "[ Stopping services ]"
        podman-compose -f "$COMPOSE_FILE" down
        ;;
    remove)
        # Stop all services and remove associated volumes
        echo "[ Removing services and volumes ]"
        podman-compose -f "$COMPOSE_FILE" down -v
        ;;
    *)
        # Handle invalid commands
        echo "[ Error ] Invalid parameter. Usage: $0 [start|restart|stop|remove] [model_name]"
        echo "You can specify an optional model name when using the 'start' command. If no model is specified, 'llama3.2' will be used by default."
        echo "To see the list of available models, visit https://ollama.com/library."
        exit 1
        ;;
esac
