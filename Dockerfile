# Use Python 3.11 slim image
#FROM python:3.11-slim
#
## Set environment variables
#ENV PYTHONUNBUFFERED=1 \
#    PYTHONDONTWRITEBYTECODE=1
#
## Set the working directory inside the container
#WORKDIR /usr/src/app
#
## Install system dependencies for PostgreSQL and build tools
#RUN apt-get update && apt-get install -y \
#    libpq-dev gcc curl && \
#    apt-get clean && rm -rf /var/lib/apt/lists/*
#
## Copy the requirements file first to leverage Docker cache
#COPY requirements.txt ./
#
## Install Python dependencies
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy the rest of the application files into the container
#COPY . .
#
## Create a non-root user and switch to it (for security)
#RUN useradd -m appuser && chown -R appuser /usr/src/app
#USER appuser
#
## Expose the port for the Django app
#EXPOSE 8000
#
## Run the Django app with Gunicorn
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "TimeSyncPro.wsgi:application"]
