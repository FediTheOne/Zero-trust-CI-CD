pipeline {
    agent any // Later we will move this to a K8s pod agent

    options {
        // Ensures a clean workspace every time, preventing leftover Git errors
        skipDefaultCheckout()
    }

    environment {
        // Use the Git Commit SHA for unique, immutable tagging
        IMAGE_TAG = "fedi-zero-trust-app:${env.GIT_COMMIT.take(7)}"
        REGISTRY_CREDENTIALS = 'my-docker-hub-creds' 
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
                // Native execution using the host's Docker engine
                sh '''
                    docker run --rm \
                    -v ${WORKSPACE}:/app \
                    aquasec/trivy:latest \
                    fs --severity HIGH,CRITICAL --exit-code 1 /app
                '''
            }
        }

        stage('Build Image') {
            steps {
                script {
                    echo "Building Docker Image natively..."
                    sh "docker build -t ${IMAGE_TAG} ."
                }
            }
        }

        stage('Push to Registry') {
            steps {
                script {
                    // Securely login using Jenkins credentials provider
                    withCredentials([usernamePassword(credentialsId: REGISTRY_CREDENTIALS, 
                                     passwordVariable: 'DOCKER_PASSWORD', 
                                     usernameVariable: 'DOCKER_USER')]) {
                        
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USER --password-stdin"
                        sh "docker push ${IMAGE_TAG}"
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up local images to prevent Jenkins agent disk bloat
            sh "docker rmi ${IMAGE_TAG} || true"
        }
    }
}
