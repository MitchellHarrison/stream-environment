# base image
FROM python:3.8-slim

# working directory
WORKDIR /output_handler

# copy requirements
COPY requirements.txt .

# update pip and install dependencies
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy all files
COPY . .

# run the app
CMD python3 src/main.py
