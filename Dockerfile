FROM python:3.11
WORKDIR /usr/src/app
COPY . .
RUN apt-get update && apt-get install -y python3-opencv
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE ${PORT:-5000}
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5000}