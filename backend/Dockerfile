# Use a lightweight Alpine-based Python image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev \
    && pip install -r requirements.txt \
    && apk del gcc python3-dev musl-dev

# # Copy the Flask application code
# COPY ./app .
# COPY ./migrations .
# COPY ./config.py .
# COPY wsgi.py .
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Command to run the Flask application (e.g., using Gunicorn)
CMD ["flask", "db", "upgrade"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
# CMD ["sh", "-c", "PYTHONPATH=/app gunicorn --bind 0.0.0.0:5000 wsgi:app"]