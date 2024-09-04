FROM continuumio/miniconda3:24.7.1-0

RUN pip install flask pygithub waitress lz4 flask-cors
COPY colaburl/server.py server.py
CMD waitress-serve --host 0.0.0.0 server:app
