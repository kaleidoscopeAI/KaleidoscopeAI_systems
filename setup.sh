#!/bin/bash
set -e  # Exit on error
LOG_FILE="setup.log"
PROJECT_DIR="/home/jg/Videos/kaleidoscope_ai_project"  # Fixed project directory path
VENV_DIR="$PROJECT_DIR/kaleidoscope_env"

echo "Starting setup..." | tee -a $LOG_FILE
echo "Project Directory: $PROJECT_DIR" | tee -a $LOG_FILE

# Function to log errors and exit
handle_error() {
    echo "Error on line $1" | tee -a $LOG_FILE
    exit 1
}
trap 'handle_error $LINENO' ERR

# Step 1: Check for and Install AWS CLI
echo "Checking AWS CLI installation..." | tee -a $LOG_FILE
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing AWS CLI v2..." | tee -a $LOG_FILE
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install || {
        echo "Failed to install AWS CLI" | tee -a $LOG_FILE
        exit 1
    }
else
    echo "AWS CLI already installed: $(aws --version)" | tee -a $LOG_FILE
fi

# Step 2: Setup Python Virtual Environment
echo "Setting up Python virtual environment..." | tee -a $LOG_FILE
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate
pip install --upgrade pip setuptools wheel || {
    echo "Failed to upgrade pip, setuptools, and wheel" | tee -a $LOG_FILE
    exit 1
}

# Step 3: Install Python Dependencies
echo "Checking if requirements.txt exists..." | tee -a $LOG_FILE
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "requirements.txt found. Installing Python dependencies..." | tee -a $LOG_FILE
    pip install -r $PROJECT_DIR/requirements.txt --default-timeout=100 --no-cache-dir || {
        echo "Failed to install Python dependencies" | tee -a $LOG_FILE
        exit 1
    }
else
    echo "ERROR: requirements.txt not found in $PROJECT_DIR" | tee -a $LOG_FILE
    ls -l $PROJECT_DIR | tee -a $LOG_FILE
    exit 1
fi

# Step 4: Install MKL from Conda-Forge
echo "Installing MKL (Intel Math Kernel Library)..." | tee -a $LOG_FILE
conda install -c conda-forge mkl=2023.1.0 -y || {
    echo "Failed to install MKL" | tee -a $LOG_FILE
    exit 1
}

# Step 5: Export Environment Variables
echo "Setting environment variables..." | tee -a $LOG_FILE
export PYTHONPATH="${PYTHONPATH}:${PROJECT_DIR}"
export PATH="${VENV_DIR}/bin:${PATH}"
echo "PYTHONPATH set to: $PYTHONPATH" | tee -a $LOG_FILE

# Add to .bashrc for permanent setup
if ! grep -q "export PYTHONPATH=${PYTHONPATH}" ~/.bashrc; then
    echo "export PYTHONPATH=${PYTHONPATH}" >> ~/.bashrc
    echo "export PATH=${VENV_DIR}/bin:${PATH}" >> ~/.bashrc
    echo "Environment variables added to .bashrc" | tee -a $LOG_FILE
fi
source ~/.bashrc

# Step 6: Fix Docker Connection and Build Image
echo "Ensuring Docker daemon is running and using the correct socket..." | tee -a $LOG_FILE
unset DOCKER_HOST  # Ensure we're using the default Docker socket
export DOCKER_HOST="unix:///var/run/docker.sock"

if ! docker ps &> /dev/null; then
    echo "Docker is not accessible. Attempting to start the Docker service..." | tee -a $LOG_FILE
    sudo systemctl start docker || {
        echo "Failed to start Docker service" | tee -a $LOG_FILE
        exit 1
    }
else
    echo "Docker is running and accessible." | tee -a $LOG_FILE
fi

echo "Building Docker image..." | tee -a $LOG_FILE
docker build -t kaleidoscope_ai:latest $PROJECT_DIR || {
    echo "Failed to build Docker image" | tee -a $LOG_FILE
    exit 1
}

# Step 7: Kubernetes Deployment
echo "Deploying to Kubernetes..." | tee -a $LOG_FILE
if kubectl version --client &> /dev/null; then
    kubectl apply -f $PROJECT_DIR/cloudFormation_Template.yaml || {
        echo "Failed to deploy to Kubernetes" | tee -a $LOG_FILE
        exit 1
    }
else
    echo "kubectl not found. Skipping Kubernetes deployment." | tee -a $LOG_FILE
fi

# Step 8: Configure GoDaddy Domain
echo "Configuring GoDaddy domain (artificialthinker.com) to point to AWS Load Balancer..." | tee -a $LOG_FILE
python $PROJECT_DIR/godaddy-credentials.py || {
    echo "Failed to configure GoDaddy domain" | tee -a $LOG_FILE
    exit 1
}

# Step 9: Initialize Quantum DynamicCube
echo "Initializing Quantum DynamicCube..." | tee -a $LOG_FILE
python $PROJECT_DIR/quantum/initialize_cube.py || {
    echo "Failed to initialize Quantum DynamicCube" | tee -a $LOG_FILE
    exit 1
}

# Step 10: Run Main Application
echo "Starting main application..." | tee -a $LOG_FILE
python $PROJECT_DIR/main.py || {
    echo "Failed to start the main application" | tee -a $LOG_FILE
    exit 1
}

# Finishing Setup
echo "Setup complete. Check $LOG_FILE for details." | tee -a $LOG_FILE

