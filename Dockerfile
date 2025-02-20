FROM ubuntu:22.04

# Avoid interaction
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace/airepeater

RUN apt-get update && apt-get install -y ffmpeg \
    software-properties-common \
    wget \
    && apt-get clean

# add deadsnakes PPA and update package list
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update

# install python3.12
RUN apt-get install -y python3.12 && \
    apt-get clean

# install pip
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.12 get-pip.py && \
    rm get-pip.py

# Check python and pip version
RUN python3.12 --version && pip --version

# Copy dependencies
COPY requirements.txt .

# Install depdendencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# App port
EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200", "--reload"]

