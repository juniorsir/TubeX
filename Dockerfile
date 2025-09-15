FROM python:3.10-slim

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/tubex /app/src/tubez

# Install python dependencies
RUN pip install .

# Expose the port
EXPOSE 8089

# Define the command to run the app
CMD ["tubez"]
