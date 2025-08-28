FROM --platform=linux/amd64 python:3.11.4 AS builder

RUN pip install poetry==1.6.1
RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root --without dev

########################################################

FROM --platform=linux/amd64 python:3.11.4-slim AS runner

# Install netcat and curl for network debug
RUN apt-get update && apt-get --no-install-recommends install -y \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ENV PYTHONPATH="/tmp:/tmp/code"
ENV MPLCONFIGDIR="/tmp"

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./app ./app
COPY .fin-gpt-cached .fin-gpt-cached
COPY .deepeval .deepeval

# Add the script to copy and start the server
RUN echo '#!/bin/bash\n\
cp -r /code /tmp/\n\
cd /tmp/code\n\
uvicorn app.server:app --host 0.0.0.0 --port 8080\n' > /code/start_server.sh

RUN chmod +x /code/start_server.sh

EXPOSE 8080

CMD ["/code/start_server.sh"]
