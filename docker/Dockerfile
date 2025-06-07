FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1    \
    PYTHONUNBUFFERED=1

# Debug things.
COPY --chmod=755 docker/stuff/packages-dev.sh docker/stuff/packages-prod.sh ./
RUN ./packages-dev.sh 2>&1 | tee /var/jellybooks/packages-dev.out
COPY --chmod=755 docker/stuff/packages-prod.sh docker/stuff/packages-prod.sh ./
RUN ./packages-prod.sh 2>&1 | tee /var/jellybooks/packages-prod.out


FROM base AS dev

WORKDIR /app
RUN useradd -ms /bin/bash dev
RUN chown -R dev:dev /app

RUN mkdir -p /var/log/jellybooks/
RUN chown dev:dev /var/log/jellybooks/

USER dev
RUN mkdir /home/dev/.ssh/ && chmod  700 /home/dev/.ssh/
COPY --chown=dev:dev --chmod=600 docker/stuff/known_hosts /home/dev/.ssh/known_hosts

COPY requirements.txt /app/
RUN virtualenv --python=python3 /home/dev/venv && . /home/dev/venv/bin/activate && pip install --upgrade pip && pip install -r /app/requirements.txt

FROM dev AS app
# Note that I'll mount a volume during dev so that I see updates.
USER dev
COPY . /app/
WORKDIR /app

# Expose the port Django will run on
EXPOSE 8200

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
