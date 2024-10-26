FROM python:3.12.7-alpine3.20 AS builder

RUN python3 -m pip install pipenv

# Tell pipenv to create venv in the current directory
ENV PIPENV_VENV_IN_PROJECT=1

# Pipfile contains requests
ADD Pipfile.lock Pipfile /usr/src/

WORKDIR /usr/src

RUN python3 -m pipenv sync

# RUN /usr/src/.venv/bin/python -c "import requests; print(requests.__version__)"

FROM python:3.12.7-alpine3.20 AS runtime

RUN mkdir -v /usr/src/.venv

COPY --from=builder /usr/src/.venv/ /usr/src/.venv/

# RUN /usr/src/.venv/bin/python -c "import requests; print(requests.__version__)"

ADD main.py /usr/src/

WORKDIR /usr/src/

# USER coolio

CMD ["./.venv/bin/python", "main.py"]