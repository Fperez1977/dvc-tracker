FROM python:3.11-slim

# System deps needed by pandas/lxml at build time
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py seed_historical_stays.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
# CORS/XSRF checks are disabled here because they're based on comparing the
# browser's Origin/Host headers to what Streamlit expects — behind the nginx
# reverse proxy those don't match the NAS's LAN IP, so Streamlit rejects the
# websocket outright ("Rejecting WebSocket connection with disallowed Origin
# or Host header"), which is why the UI got stuck on the loading skeleton.
# The nginx layer (with its Basic Auth) is what actually guards access now.
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.gatherUsageStats=false"]
