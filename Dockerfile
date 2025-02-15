FROM python:3.12-slim-bookworm 

# Install required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm

# Install specific version of Prettier
RUN npm install -g prettier@3.4.2

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy application files
WORKDIR /app
COPY src/hello.py /app/
COPY requirements.txt /app/

# Install dependencies using uv
RUN uv pip install --system -r requirements.txt

# Run the application
CMD ["uv", "run", "hello.py"]
