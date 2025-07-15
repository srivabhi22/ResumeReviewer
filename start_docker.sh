# ====== Docker Commands ======
echo "Building backend image..."
docker build -t backend -f backend/Dockerfile .

echo "Building frontend image..."
docker build -t frontend -f frontend/Dockerfile .

echo "Starting Docker Compose with build..."
docker compose up --build


# use command $bash .\start_docker.sh to run bash script git bash or WSL
# use command $bash ./start_docker.sh to run bash script on Linux or macOS                                                                                                                                                                     



