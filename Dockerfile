FROM runpod/base:0.6.3-cuda11.8.0

# Set python3.11 as the default python
RUN ln -sf $(which python3.12) /usr/local/bin/python && \
    ln -sf $(which python3.12) /usr/local/bin/python3

# Install dependencies
COPY requirements.txt /requirements.txt
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system

# Add files
ADD handler.py .
ADD src /app/src

# Run the handler
CMD python -u /handler.py