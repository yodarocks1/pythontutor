FROM ubuntu:jammy

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip install json-fix
RUN pip install django
RUN pip install requests
RUN mkdir -p /home/pythontutor

COPY . /home/pythontutor
WORKDIR /home/pythontutor

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

