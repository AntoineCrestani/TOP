FROM python:3.10-slim-bullseye
COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /src

COPY . .
ENTRYPOINT [ "python", "Dash_app_TOP.py" ]