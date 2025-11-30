# 1. Use an official Python slim image as the base
# Using a specific version (like 3.11) is better than just 'python:latest'
FROM python:3.11-slim

# 2. Set the working directory inside the container
# This is where your app's code will live
WORKDIR /app

# 3. Copy just the requirements file first to leverage Docker cache
# If requirements.txt doesn't change, Docker won't re-install dependencies
COPY requirements.txt .

# 4. Install Python dependencies
# --no-cache-dir keeps the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# 6. Expose the port your app will run on (e.g., 5000 for Flask)
EXPOSE 5000

# 7. Specify the command to run when the container starts
# Note: 'host="0.0.0.0"' is crucial to make the app accessible
# from outside the container.
CMD ["python", "main.py"]