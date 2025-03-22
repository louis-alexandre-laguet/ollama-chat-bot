import os
import shutil
import aiofiles
import asyncio
from typing import List
from asyncio import gather
from fastapi import Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse

from services import Services
from prompt_request import PromptRequest

services = Services()
app = services.get_app()
logger = services.get_logger()
templates = services.get_templates()
response_generator = services.get_response_generator()
document_indexer = services.get_document_indexer()
database_manager = services.get_database_manager()


# Route to serve the main index HTML page
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    logger.debug("Serving index.html page.")
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/set-system-prompt/")
async def set_system_prompt_api(request: Request):
    try:
        # Parse the incoming JSON request data
        data = await request.json()
        system_prompt = data.get('system_prompt')

        # Set the system prompt in the response generator
        response_generator.set_system_prompt(system_prompt)
        logger.info("System prompt set successfully.")
        return {"message": "System prompt set successfully."}

    except Exception as e:
        logger.error(f"Failed to set system prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to set system prompt.")


@app.post("/upload-documents/")
async def upload_documents_api(files: List[UploadFile] = File(...)):
    # Define the path for the temporary directory
    temp_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../resources/data"))
    os.makedirs(temp_directory, exist_ok=True)

    try:
        # Asynchronous function to save a file
        async def save_file(file: UploadFile):
            file_path = os.path.join(temp_directory, file.filename)
            async with aiofiles.open(file_path, "wb") as buffer:
                content = await file.read()
                await buffer.write(content)
            return file_path

        # Save the files asynchronously
        tasks = [save_file(file) for file in files]
        file_paths = await gather(*tasks)

        # Index the documents asynchronously (if available)
        if hasattr(document_indexer, "index_documents_async"):
            await document_indexer.index_documents_async(file_paths)
        else:
            # If asynchronous indexing is not available, use a thread for synchronous indexing
            await asyncio.to_thread(document_indexer.index_documents, temp_directory)

        logger.info("Documents uploaded and indexed successfully.")
        return {"message": "Documents uploaded and indexed successfully."}

    except Exception as e:
        logger.error(f"Failed to index uploaded documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to index uploaded documents.")

    finally:
        # Clean up by removing the temporary directory and its contents
        try:
            shutil.rmtree(temp_directory)
            logger.info("Temporary files cleaned up successfully.")
        except Exception as e:
            logger.error(f"Failed to delete temporary directory {temp_directory}: {e}")


@app.post("/toggle-rag/")
async def toggle_rag_api(request: Request):
    data = await request.json()
    enable_rag = data.get('enableRAG')

    if enable_rag is None:
        raise HTTPException(status_code=400, detail="Missing 'enableRAG' parameter.")

    if enable_rag:
        if services.is_rag_enabled():
            raise HTTPException(status_code=400, detail="RAG is already enabled.")
        services.set_rag_enabled(True)
        message = "RAG enabled successfully."
    else:
        if not services.is_rag_enabled():
            raise HTTPException(status_code=400, detail="RAG is already disabled.")
        services.set_rag_enabled(False)
        message = "RAG disabled successfully."

    logger.info(message)
    return {"message": message}


@app.post("/generate-response/")
async def generate_response_api(request: PromptRequest):
    services.set_generating_response(True)
    prompt = request.prompt
    top_n = request.top_n if request.top_n is not None else 3
    num_ctx = request.num_ctx
    temperature = request.temperature
    repeat_last_n = request.repeat_last_n
    repeat_penalty = request.repeat_penalty

    # Sanitize values to ensure they fall within appropriate limits
    num_ctx = max(1, min(4096, num_ctx))
    temperature = max(0, min(2, temperature))
    repeat_last_n = max(1, min(1024, repeat_last_n))
    repeat_penalty = max(1, min(2, repeat_penalty))
    top_n = max(1, min(10, top_n))

    # Log the received prompt and parameters
    logger.info(f"Received prompt: {prompt} with top_n: {top_n}, num_ctx: {num_ctx}, "
                f"temperature: {temperature}, repeat_last_n: {repeat_last_n}, "
                f"repeat_penalty: {repeat_penalty}")

    async def generate():
        if services.is_rag_enabled():
            logger.debug("Using RAG-enabled response generation.")
            # Use RAG-based response generation
            async for chunk in response_generator.generate_response_with_retriever(
                prompt, 
                top_n=top_n,
                num_ctx=num_ctx,
                temperature=temperature,
                repeat_last_n=repeat_last_n,
                repeat_penalty=repeat_penalty
            ):
                logger.debug(f"Generated chunk: {chunk}")
                yield chunk
        else:
            logger.debug("Using standard response generation.")
            # Use standard response generation
            async for chunk in response_generator.generate_response(
                prompt, 
                num_ctx=num_ctx,
                temperature=temperature,
                repeat_last_n=repeat_last_n,
                repeat_penalty=repeat_penalty
            ):
                logger.debug(f"Generated chunk: {chunk}")
                yield chunk

        services.set_generating_response(False)

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/stop-generation")
async def stop_generation():
    response_generator.stop_generation = True
    return {"message": "Generation stopped."}


@app.post("/cleanup-database/")
async def cleanup_database_api():
    try:
        # Clean up the database by deleting records and resetting the FAISS index
        database_manager.clean_database()
        logger.info("Database cleaned successfully.")
        return {"message": "Database cleaned successfully."}

    except Exception as e:
        logger.error(f"Failed to clean the database: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean the database.")


# Entry point to run the FastAPI application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
