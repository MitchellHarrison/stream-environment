# base image
FROM python:3.8-slim

# working directory
WORKDIR /app

# copy requirements to image
COPY requirements.txt .

# install dependencies
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt 2>&1

# copy all files to imagee
COPY . .

# run app
CMD python3 src/main.py
