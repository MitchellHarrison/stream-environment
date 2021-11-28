# base image
FROM python:3.8-slim

# working directory
WORKDIR /input_handler

# copy requirements
COPY requirements.txt .

# update pip and install requirements
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy all files
COPY . .

# run app
CMD ["python3", "-u", "src/main.py"]
