# Stage 0 - Create from Python3.9.7 image
FROM python:3.8.16 as stage0

# Stage 2 - Create virtual environment and install dependencies
FROM stage0 as stage1
COPY requirements.txt /app/requirements.txt
RUN /usr/local/bin/python3 -m venv /app/env
RUN /app/env/bin/pip install -r /app/requirements.txt

# Stage 1 - Copy MetroMan code
FROM stage1 as stage2
COPY pair_obs.py /app/pair_obs.py
LABEL version="1.0" \
	description="Containerized SWOT Observation Pairing with HLS." \
	"confluence.contact"="travissimmons@umass.edu"
ENTRYPOINT ["/app/env/bin/python3", "/app/pair_obs.py"]