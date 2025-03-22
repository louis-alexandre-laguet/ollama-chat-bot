import os
import json
import aiohttp

class ResponseGenerator:
    """
    A class to manage and generate responses based on a given prompt, using various model settings.
    It can also augment the prompt with retrieved documents to provide additional context.
    """

    def __init__(self, logger=None, model=None, master_prompt=None, system_prompt=None, document_retriever=None):
        # Initialize custom logger
        self.logger = logger

        # Initialize global variables
        self.model = model
        self.master_prompt = master_prompt
        self.system_prompt = system_prompt
        self.document_retriever = document_retriever
        self.stop_generation = False

    
    def set_model(self, model):
        """
        Set the model globally.

        Args:
            model (str): The model to use.
        """
        self.model = model
        self.logger.debug(f"Model set to: {self.model}")

    
    def set_master_prompt(self, master_prompt):
        """
        Set the master prompt text globally.

        Args:
            master_prompt (str): The master prompt text to set.
        """
        self.master_prompt = master_prompt
        self.logger.debug(f"Master prompt set to: {self.master_prompt}")

    
    def set_system_prompt(self, system_prompt):
        """
        Set the system prompt text globally.

        Args:
            system_prompt (str): The system prompt text to set.
        """
        self.system_prompt = system_prompt
        self.logger.debug(f"System prompt set to: {self.system_prompt}")

    
    async def generate_response(self, prompt, num_ctx, temperature, repeat_last_n, repeat_penalty):
        """
        Generate a response asynchronously based on a given prompt.
        Sends a request to an external API for text generation using a specified model and streams the response back.

        Args:
            prompt (str): The input prompt to generate a response for.
            num_ctx (int): Sets the size of the context window used to generate the next token.
            temperature (float): Adjusts the creativity of the model's responses. Higher values lead to more creative outputs.
            repeat_last_n (int): Sets how far back the model looks to prevent repetition.
            repeat_penalty (float): Controls the penalty for repetitions. A higher value penalizes repetitions more strongly.

        Yields:
            str: Chunks of the generated response.
        """
        full_prompt = f"""
{self.master_prompt}

System Instructions:
{self.system_prompt or 'No specific system instructions provided.'}

User Question:
{prompt}

Context Documents:
No relevant documents provided.
"""

        url = f"http://{os.getenv('OLLAMA_HOST')}:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "options": {
                "num_ctx": num_ctx,
                "temperature": temperature,
                "repeat_last_n": repeat_last_n,
                "repeat_penalty": repeat_penalty
            }
        }

        self.logger.info(f"Generating response")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    async for line in response.content:
                        if self.stop_generation:
                            self.stop_generation = False
                            break
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if data.get('done', False):
                                    break
                                yield data.get('response', '')
                            except json.JSONDecodeError as e:
                                self.logger.error(f"JSONDecodeError: {e}")
                                yield "Error decoding JSON"
            except aiohttp.ClientError as e:
                self.logger.error(f"ClientError: {e}")
                yield "An error occurred regarding the Ollama container."

    
    async def generate_response_with_retriever(self, prompt, top_n, num_ctx, temperature, repeat_last_n, repeat_penalty):
        """
        Generate a response using retrieved documents to provide additional context.
        Retrieves a specified number of relevant documents based on the input prompt, 
        augments the prompt with this context, and then generates a response using the augmented prompt.

        Args:
            prompt (str): The input prompt to generate a response for.
            top_n (int): The number of documents to retrieve for providing context.
            num_ctx (int): Sets the size of the context window used to generate the next token.
            temperature (float): Adjusts the creativity of the model's responses. Higher values lead to more creative outputs.
            repeat_last_n (int): Sets how far back the model looks to prevent repetition.
            repeat_penalty (float): Controls the penalty for repetitions. A higher value penalizes repetitions more strongly.

        Yields:
            str: Chunks of the generated response.
        """
        self.logger.info(f"Retrieving documents")

        # Retrieve documents based on the input prompt
        documents = self.document_retriever.retrieve_documents(prompt, top_n)

        if not documents:
            self.logger.warning("No relevant documents found, continuing with just the prompt.")
            documents = ["No relevant documents found."]

        # Augment the prompt with retrieved documents
        augmented_prompt = f"""
{self.master_prompt}

System Instructions:
{self.system_prompt or 'No specific system instructions provided.'}

Context Documents:
{'\n'.join(documents) if documents else 'No relevant documents provided.'}

User Question:
{prompt}
"""

        async for chunk in self.generate_response(augmented_prompt, num_ctx, temperature, repeat_last_n, repeat_penalty):
            yield chunk
