# --------------BASE STAGE--------------#
FROM python:3.12.3-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


#--------------DEVELOPMENT STAGE--------------#
FROM base AS dev

# Copy the source code into the container.
COPY . . 

# Expose the port that the application listens on & run the application.
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


#--------------PRODUCTION STAGE--------------#
FROM base AS prod

RUN addgroup --system app && adduser --system --group app
USER app

COPY ./apps /app/apps
COPY ./config /app/config
COPY ./manage.py /app/manage.py

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

RUN python manage.py collectstatic --no-input 

# Expose port and run with a production-ready server like Gunicorn
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
