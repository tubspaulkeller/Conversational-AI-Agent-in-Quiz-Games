FROM rasa/rasa:3.3.0

# Copy the Rasa files to the container
COPY . /app

# Set the working directory
WORKDIR /app

USER root
COPY ./actions/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install -r requirements.txt

# Start the Rasa server
# Train the Rasa model
RUN rasa train

VOLUME /app/models

