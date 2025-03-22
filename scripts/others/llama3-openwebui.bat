@echo off
REM ========================================
REM Script to run Ollama with Open-WebUI
REM ========================================

REM Start Ollama container
echo [ Starting Ollama ]
podman run -d --name ollama --replace --pull=always --restart=always ^
    -p 127.0.0.1:11434:11434 -v ollama:/root/.ollama --stop-signal=SIGKILL ^
    docker.io/ollama/ollama

REM Pull the llama3.2:3B model
echo [ Running llama3.2:3B model ]
podman exec -it ollama ollama run llama3.2

REM Start Open-WebUI container
echo [ Starting Open-WebUI ]
podman run -d --name open-webui --replace --pull=always --restart=always ^
    -p 127.0.0.1:3000:8080 --network=pasta:-T,11434 --add-host=ollama.local:127.0.0.1 ^
    -e OLLAMA_BASE_URL=http://ollama.local:11434 -v open-webui:/app/backend/data ^
    ghcr.io/open-webui/open-webui:main

REM Open the Open-WebUI web interface in the default web browser
echo [ Opening Open-WebUI web interface ]
start "" "http://localhost:3000"

REM Wait for user input to shut down containers
echo Press any key to shut down Open-WebUI and Ollama...
pause >nul

REM Remove containers and volumes
podman rm -f open-webui ollama
podman volume rm -f open-webui ollama
