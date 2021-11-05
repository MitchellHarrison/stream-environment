# base image
FROM python:3.8-slim

# requirements
WORKDIR /project

# copy and install requirements
COPY requirements.txt .
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy project files
COPY . .

# run the app
CMD python3 src/main.py
