pipeline {
    agent any // Later we will move this to a K8s pod agent

    environment {
        // Use the Git Commit SHA for unique, immutable tagging
        IMAGE_TAG = "myapp:${env.GIT_COMMIT.take(7)}"
        REGISTRY_CREDENTIALS = 'my-docker-hub-creds' 
    }

    stages {
        stage('Initialize'){
            steps {
                script {
                    def dockerHome = tool 'myDocker'
                    env.PATH = "${dockerHome}/bin:${env.PATH}"
                }
            }
            
        }

        stage('Debug Paths') {
            steps {
                    sh 'ls -la ${WORKSPACE}'
                    sh 'pwd'
            }
        }
		
	    stage('SCA Security Scan') {
            steps {
                sh '''
                    wget -q https://github.com/aquasecurity/trivy/releases/latest/download/trivy_$(uname -s)_64bit.tar.gz
                    tar zxvf trivy_*_64bit.tar.gz
                    chmod +x trivy
                    ./trivy fs --severity HIGH,CRITICAL --exit-code 1 .
                '''
  }
}

        stage('Build Image') {
            steps {
                script {
                    echo "Building Docker Image via Shell..."
                    sh "docker build -t fedi-zero-trust-app:${env.BUILD_ID} ."
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