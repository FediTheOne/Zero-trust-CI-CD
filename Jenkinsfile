pipeline {
    agent any 

    environment {
        // The secure target directory on the Ubuntu host where the app will live
        DEPLOY_DIR = "/opt/zero-trust-app"
    }

    stages {
        stage('Clean & Checkout') {
            steps {
                cleanWs() 
                checkout scm 
            }
        }

        stage('SCA Security Scan') {
            steps {
                echo "Running Native Trivy Scan on the Host..."
                // Executes natively on Ubuntu without Docker
                sh "trivy fs --severity HIGH,CRITICAL --exit-code 1 ."
            }
        }

        stage('Build & Verify Venv') {
            steps {
                echo "Building isolated Python Virtual Environment..."
                sh '''
                    python3 -m venv venv
                    ./venv/bin/pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Secure Deployment') {
            steps {
                echo "Deploying and applying Host-Based Security Controls..."
                sh '''
                    # Create deployment directory if it doesn't exist
                    sudo mkdir -p ${DEPLOY_DIR}
                    
                    # Copy application files and the verified virtual environment
                    sudo cp -r . ${DEPLOY_DIR}
                    
                    # Enforce strict ownership: appuser owns it, nobody else can modify it
                    sudo chown -R appuser:appgroup ${DEPLOY_DIR}
                    sudo chmod -R 750 ${DEPLOY_DIR}
                '''
            }
        }
    }
}