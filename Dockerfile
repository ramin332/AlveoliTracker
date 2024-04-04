# Use the official Python image from the Docker Hub
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Set Python to run unbuffered
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8050

# Copy the entire app directory contents into the container
COPY app/ .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user 'myuser'
RUN useradd -m myuser

# Change ownership of the /app directory to 'myuser'
RUN chown -R myuser:myuser /app

# Switch to 'myuser'
USER myuser

# Define the command to run the Python script
CMD ["python", "alveolus_visualizer.py"]
