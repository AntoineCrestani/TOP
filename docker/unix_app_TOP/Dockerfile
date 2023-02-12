FROM python:3.10-slim-bullseye
COPY . .
RUN ./mongo_setup.sh
RUN pip install  -r ./src/requirements.txt

WORKDIR /

EXPOSE 8050
ENTRYPOINT [ "python", "./src/Dash_app_TOP.py" ]