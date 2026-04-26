pipeline {
    agent any // Later we will move this to a K8s pod agent

    environment {
        // Use the Git Commit SHA for unique, immutable tagging
        IMAGE_TAG = "myapp:${env.GIT_COMMIT.take(7)}"
        REGISTRY_CREDENTIALS = 'my-docker-hub-creds' 
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
		
		stage('SCA Security Scan') {
			steps {
				script {
					// We use --severity HIGH,CRITICAL to only block dangerous builds
					// --exit-code 1 tells Jenkins to mark the stage as FAILED if findings exist
					sh "docker run --rm -v \$(pwd):/apps aquasec/trivy:latest fs --severity HIGH,CRITICAL --exit-code 1 /apps"
				}
			}
		}

        stage('Build Image') {
            steps {
                script {
                    // This command triggers the multi-stage build you just checked
                    sh "docker build -t ${IMAGE_TAG} ."
                }
            }
        }

        stage('Security Scan') {
            steps {
                echo "Phase 3 preview: We will put Trivy/Snyk scans here shortly."
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