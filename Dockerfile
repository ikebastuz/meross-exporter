# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 1400 available to the world outside this container
EXPOSE 1400

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "metrics.py"]