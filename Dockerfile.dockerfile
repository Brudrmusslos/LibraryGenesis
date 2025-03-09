FROM python:3.9-slim

WORKDIR /app

# Install git to clone the repository
RUN apt-get update && apt-get install -y git && apt-get clean

# Clone the repository directly from GitHub
RUN git clone https://github.com/Brudrmusslos/LibraryGenesis.git /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Expose the application's port (if needed)
EXPOSE 8003

# Run the application
CMD ["python", "/app/server.py"]
