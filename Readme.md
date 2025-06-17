install miniconda
add it into environment variable
open cmd -> goto project folder
conda create -p venv python=3.12
conda init
close the cmd and take it again
conda activate C:\Users\Hameed\Desktop\Anomaly_detection\venv 
venv will be activated
come to project directory in vscode
open terminal
python file.py
pip install -r requirements.txt

# Stop all containers
docker-compose down

# Remove unused data
docker system prune -a

# Full rebuild
docker-compose up --build
