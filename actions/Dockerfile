FROM rasa/rasa-sdk:2.8.0
WORKDIR /app
COPY requirements.txt requirements.txt
USER root
RUN pip install -r requirements.txt
EXPOSE 5058
USER 1001
