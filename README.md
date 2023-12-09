# Docker environment
```
sudo apt-get install docker
sudo docker pull yodarocks1/pythontutor:latest
sudo docker run -it -p 8000:8000 pythontutor:latest
```
Problems: [localhost:8000/problems](localhost:8000/problems)
Admin: [localhost:8000/admin](localhost:8000/admin)
- Login:
 - Username: `admin`
 - Password: `demo`


# Manual installation
## Setup
```
git clone git@github.com:yodarocks1/pythontutor.git
cd pythontutor
pip install json-fix
pip install django
pip install requests
pip install RestrictedPython
```

## Run
```
python3 manage.py runserver 0.0.0.0:8000
```
Open: [localhost:8000/problems](localhost:8000/problems)

## Edit Problems
```
python3 manage.py createsuperuser 0.0.0.0:8000
```
Open: [localhost:8000/admin](localhost:8000/admin)
