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

        stage('Secret Scan (gitleaks)') {
            steps {
                echo "Scanning git history for committed secrets..."
                sh '''
                docker run --rm \
                -v "$(pwd):/repo:ro" \
                zricethezav/gitleaks:v8.21.2 \
                detect \
                    --source=/repo \
                    --no-banner \
                    --verbose \
                    --exit-code=1
                '''
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
                   --timeout 15m \
                   /scan
            '''
            }
        }

        stage('SAST Scan (Semgrep)') {
            steps {
                echo "Running Semgrep static analysis..."
                sh '''
                docker run --rm \
                -v "$(pwd):/src:ro" \
                returntocorp/semgrep:1.99.0 \
                semgrep scan \
                    --config=p/security-audit \
                    --config=p/secrets \
                    --config=p/python \
                    --config=p/flask \
                    --severity=ERROR \
                    --error \
                    --metrics=off \
                    /src
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

        stage('Docker Push') {
            steps {
                echo "Pushing image to Docker Hub..."
                withCredentials([usernamePassword(
                credentialsId: 'dockerhub-creds',
                usernameVariable: 'DOCKERHUB_USER',
                passwordVariable: 'DOCKERHUB_TOKEN'
            )]) {
            sh '''
                echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                docker push feditheone2050/zero-trust-app:${BUILD_NUMBER}
                docker logout
            '''
                }
            }
        }

       stage('Sign Image (Cosign)') {
            steps {
            echo "Signing image with Cosign..."
            withCredentials([
            file(credentialsId: 'cosign-key', variable: 'COSIGN_KEY_FILE'),
            string(credentialsId: 'cosign-password', variable: 'COSIGN_PASSWORD'),
            usernamePassword(
                credentialsId: 'dockerhub-creds',
                usernameVariable: 'DOCKERHUB_USER',
                passwordVariable: 'DOCKERHUB_TOKEN'
            )
        ]) {
            sh '''
                # Copy the key to a location readable by the cosign container's user
                TMPKEY=$(mktemp)
                cp "$COSIGN_KEY_FILE" "$TMPKEY"
                chmod 644 "$TMPKEY"

                # Ensure the temp key is removed on exit, even if cosign fails
                trap 'rm -f "$TMPKEY"' EXIT

                # Login so cosign can push the signature
                echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin

                # Sign the image
                docker run --rm \
                    -e COSIGN_PASSWORD="$COSIGN_PASSWORD" \
                    -v "$TMPKEY:/cosign.key:ro" \
                    -v "$HOME/.docker:/root/.docker:ro" \
                    gcr.io/projectsigstore/cosign:v2.4.1 \
                    sign \
                        --key /cosign.key \
                        --yes \
                        feditheone2050/zero-trust-app:${BUILD_NUMBER}

                docker logout
                '''
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying hardened container from registry..."
                sh '''
                # Stop and remove previous instance (ephemeral trust — no carry-over state)
                docker stop zero-trust-app-cicd 2>/dev/null || true
                docker rm zero-trust-app-cicd 2>/dev/null || true

                # Pull from registry — proves the artifact passed the full chain
                docker pull feditheone2050/zero-trust-app:${BUILD_NUMBER}

                # Run with full zero-trust runtime hardening
                docker run -d \
                --name zero-trust-app-cicd \
                -p 8082:8080 \
                --read-only \
                --tmpfs /tmp:rw,noexec,nosuid,size=64m \
                --cap-drop=ALL \
                --security-opt=no-new-privileges \
                --memory=512m \
                --cpus=1.0 \
                --pids-limit=100 \
                --restart=unless-stopped \
                feditheone2050/zero-trust-app:${BUILD_NUMBER}

                # Verify it's running
                sleep 3
                docker ps --filter "name=zero-trust-app-cicd" --filter "status=running" | grep zero-trust-app-cicd
            '''
            }
        }
    }
}