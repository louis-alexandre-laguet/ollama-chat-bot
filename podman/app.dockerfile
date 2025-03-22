# Use of blueshoe's Python 3.12 slim image
FROM quay.io/blueshoe/python3.12-slim:latest

# Environment variable to disable specific optimizations
ENV TF_ENABLE_ONEDNN_OPTS=0

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY ./requirements.txt /app/

# Install the Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the 'all-MiniLM-L6-v2' model and NLTK resources
RUN python -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('all-MiniLM-L6-v2'); model.save('/app/models/all-MiniLM-L6-v2')" && \
    python -c "import nltk; \
    nltk.download('stopwords'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"

# Copy the source files
COPY ./src/ /app/src/

# Copy the database folder
COPY ./data/ /app/data/

# Switch working directory to /app/src/python/
WORKDIR /app/src/python/
