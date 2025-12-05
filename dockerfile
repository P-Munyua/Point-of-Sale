# Use Python 3.10
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SUPERUSER_USERNAME=admin2
ENV DJANGO_SUPERUSER_EMAIL=admin2@gmail.com
ENV DJANGO_SUPERUSER_PASSWORD=1234

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create entrypoint script with better superuser handling
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Apply database migrations\n\
echo "Applying migrations..."\n\
python manage.py migrate --noinput\n\
\n\
# Create superuser if it doesn'\''t exist\n\
echo "Checking for superuser..."\n\
if python manage.py shell -c "\n\
from django.contrib.auth import get_user_model\n\
User = get_user_model()\n\
try:\n\
    User.objects.get(username=\"'\''$DJANGO_SUPERUSER_USERNAME'\''\")\n\
    print('\''Superuser already exists'\'')\n\
except User.DoesNotExist:\n\
    print('\''Creating superuser...'\'')\n\
    User.objects.create_superuser('\''$DJANGO_SUPERUSER_USERNAME'\'', '\''$DJANGO_SUPERUSER_EMAIL'\'', '\''$DJANGO_SUPERUSER_PASSWORD'\'')\n\
    print('\''Superuser created successfully'\'')\n\
except Exception as e:\n\
    print(f'\''Error checking superuser: {e}'\'')\n\
"; then\n\
    echo "Superuser check completed"\n\
else\n\
    echo "Warning: Superuser creation failed, but continuing..."\n\
fi\n\
\n\
# Start server\n\
echo "Starting server..."\n\
python manage.py runserver 0.0.0.0:8002\n\
' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose the port
EXPOSE 8002

# Use the entrypoint script
CMD ["/app/entrypoint.sh"]