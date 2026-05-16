pipeline {
    agent any // Later we will move this to a K8s pod agent

    options {
        // Ensures a clean workspace every time, preventing leftover Git errors
        skipDefaultCheckout()
    }

    environment {
        // Safely fall back to the Jenkins BUILD_NUMBER if GIT_COMMIT is missing
        IMAGE_TAG = "fedi-zero-trust-app:${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : env.BUILD_NUMBER}"
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
            script {
                // Check if the variable actually exists before trying to delete it
                if (env.IMAGE_TAG) {
                    echo "Cleaning up image: ${env.IMAGE_TAG}"
                    sh "docker rmi ${env.IMAGE_TAG} || true"
                } else {
                    echo "No image tag found. Skipping cleanup."
                }
            }
        }
    }
}    