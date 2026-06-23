# Docker Setup Guide — Pull & Run

Run the ISL Translator directly from Docker Hub without cloning or building anything.

---

## Prerequisites

| Requirement | How to check |
|-------------|--------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20+) | `docker --version` |
| Docker Compose (v2+) | `docker compose version` |
| A free [Groq API key](https://console.groq.com/) | — |

> Make sure Docker Desktop is **running** before proceeding.

---

## Step 1: Create a project folder

```bash
mkdir isl-translator && cd isl-translator
```

---

## Step 2: Create the `docker-compose.yml`

Create a file named `docker-compose.yml` with the following content:

```yaml
services:
  backend:
    image: hansaj19/isl-translator-backend:latest
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=gsk_your_actual_key_here
      - GROQ_MODEL=llama-3.3-70b-versatile
      - CORS_ORIGINS=http://localhost:5173,http://localhost:80
      - MODEL_PATH=model/isl_model_2hand.tflite
      - LABELS_PATH=model/labels_2hand.json
      - STABILITY_FRAMES=5
      - BUFFER_TIMEOUT_SECONDS=5.0
      - MIN_BUFFER_SIZE=3
      - CONFIDENCE_THRESHOLD=80.0
      - HOST=0.0.0.0
      - PORT=8000
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s

  frontend:
    image: hansaj19/isl-translator-frontend:latest
    ports:
      - "5173:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```
---

## Step 3: Pull and run

```bash
docker compose up
```

Docker will automatically pull both images from Docker Hub on the first run. You should see:

```
backend-1   | INFO: Loading frame processor (MediaPipe)...
backend-1   | INFO: Loading sign classifier (TFLite)...
backend-1   | INFO: Backend ready — model: model/isl_model_2hand.tflite, classes: 35
backend-1   | INFO: Uvicorn running on http://0.0.0.0:8000
frontend-1  | Configuration complete; ready for start up
```

---

## Step 4: Open in browser

| Service | URL |
|---------|-----|
| **Frontend (App)** | http://localhost:5173 |
| **Backend API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

### Using the App

1. Allow camera access when prompted by the browser
2. Click **Start** to begin sign detection
3. Sign ISL letters — characters appear in the live buffer
4. After 5 seconds of inactivity, the buffer is sent to the LLM for word correction
5. Click **Next Word** to manually submit a word
6. Click **Finish Sentence** to get an AI-refined sentence
7. Click **Clear** to reset everything

---

## Step 5: Stop

```bash
docker compose down
```

---

## Troubleshooting

### "Cannot connect to the Docker daemon"
Docker Desktop is not running. Start it from your taskbar or applications.

### Backend container keeps restarting
Check the logs:
```bash
docker compose logs backend
```
Common causes:
- Invalid or missing `GROQ_API_KEY` in `docker-compose.yml`

### Frontend shows "Disconnected" status
The backend health check takes up to 30 seconds. Wait for the backend to become healthy before the frontend starts.

### Camera not working
- Ensure your browser has camera permissions enabled
- Use a Chromium-based browser (Chrome, Edge) for best WebRTC support
- Check that no other application is using the camera

### Port already in use
Edit the `ports` in `docker-compose.yml`:
```yaml
ports:
  - "3000:80"    # Change frontend to port 3000
  - "9000:8000"  # Change backend to port 9000
```
