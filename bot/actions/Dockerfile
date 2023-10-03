# Basisimage
FROM rasa/rasa-sdk:3.3.0

# Arbeitsverzeichnis im Container
WORKDIR /app


# Kopieren der Aktionsserver-Dateien in den Container
COPY . /app/actions

USER root
# Installieren von Third-Party-Packages
COPY requirements.txt requirements.txt
RUN pip install --verbose -r requirements.txt

USER 1001
