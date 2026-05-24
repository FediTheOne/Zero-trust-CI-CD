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
                echo "Running Trivy filesystem scan in isolated container..."
                sh '''
                docker run --rm \
                -v "$(pwd):/scan:ro" \
                -v trivy-cache:/root/.cache/ \
                aquasec/trivy:0.56.2 \
                fs --severity HIGH,CRITICAL \
                   --exit-code 1 \
                   --no-progress \
                   /scan
            '''
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

        stage('Image Security Scan (Trivy)') {
            steps {
                echo "Scanning built Docker image for vulnerabilities..."
                sh '''
                docker run --rm \
                -v /var/run/docker.sock:/var/run/docker.sock \
                -v trivy-cache:/root/.cache/ \
                aquasec/trivy:0.56.2 \
                image --severity HIGH,CRITICAL \
                      --exit-code 1 \
                      --no-progress \
                      --timeout 15m \
                      feditheone2050/zero-trust-app:${BUILD_NUMBER}
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