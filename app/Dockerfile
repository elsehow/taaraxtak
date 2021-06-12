FROM python:3

# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN ["python", "create_tables.py"]

CMD ["python", "./collect.py"]