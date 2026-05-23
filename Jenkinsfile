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

        stage('Docker Build') {
            steps {
                echo "Building Docker image..."
                sh '''
                    docker build \
                    -t feditheone2050/zero-trust-app:${BUILD_NUMBER} \
                    -t feditheone2050/zero-trust-app:latest \
                .
                '''
            }
        }

        stage('Secure Deployment') {
            steps {
                echo "Deploying and applying Host-Based Security Controls..."
                sh '''
                    # No sudo needed! Jenkins naturally has permission to write to this path now.
                    cp -r ./* /opt/zero-trust-app/
                    
                    # Ensure the copied files maintain strict 750 permissions
                    chmod -R 750 /opt/zero-trust-app/
                '''
            }
        }
    }
}