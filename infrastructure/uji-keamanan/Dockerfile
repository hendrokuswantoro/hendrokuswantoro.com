FROM python:3.12-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin hk \
 && mkdir -p /run/hk-api /srv/hendrokuswantoro/unggahan /srv/hendrokuswantoro/app/cadangan \
 && chown hk:hk /run/hk-api /srv/hendrokuswantoro/unggahan /srv/hendrokuswantoro/app/cadangan
USER hk
HEALTHCHECK --interval=10s --timeout=3s CMD ["python", "-c", "import socket; s = socket.socket(socket.AF_UNIX); s.connect('/run/hk-api/api.sock')"]
