FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --proxy-headers / --forwarded-allow-ips : le backend n'est joint que par le
# conteneur `frontend` (Nginx), qui transmet l'IP visiteur dans X-Forwarded-For.
# 172.16.0.0/12 couvre les réseaux Docker ; sans lui Uvicorn ignorerait l'en-tête
# et le throttle de connexion (voir app/core/throttle.py) verrait toujours la même
# adresse interne, partagée entre tous les visiteurs. Si un reverse proxy placé
# devant l'application se connecte depuis une autre adresse, ajoutez-la à la liste.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "172.16.0.0/12"]
