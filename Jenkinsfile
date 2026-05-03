pipeline {
    agent any
    environment {
        EC2_STAGING_IP        = '13.233.101.249'
        EC2_PROD_IP = '65.1.130.135'
        EC2_USER        = 'ec2-user'              // use ubuntu if Ubuntu AMI
        SSH_KEY_ID      = 'ec2-ssh-key'          // Jenkins credentials ID
        IMAGE_NAME      = 'preritsharma/cicdimage'
        DB_URL = 'postgresql://admin123:Password123@myrds.c3aomo0g2iyj.ap-south-1.rds.amazonaws.com:5432/mydb'
    }
    stages {

        stage('Code Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'Githubcred',
                    url: 'https://github.com/Prerit1221/8byte-devops.git'
                echo "Code Checkout is done"
            }
        }

        stage('Test') {
            steps {
                sh '''
                    source venv/bin/activate
                    pip install pytest pytest-cov
                    pytest --cov=app --cov-report=xml
                '''
            }
        }

        stage('SonarQube Analysis') {
    steps {
        withSonarQubeEnv('SonarQube') {
            withEnv(["PATH+SONAR=${tool 'SonarScanner'}/bin"]) {
                sh '''
                    sonar-scanner \
                      -Dsonar.projectName="DevOps Pipeline" \
                      -Dsonar.projectKey=8byte-devops-pipeline \
                      -Dsonar.sources=app \
                      -Dsonar.python.coverage.reportPaths=coverage.xml
                '''
            }
        }
    }
}

stage('Docker Image Build') {
            steps {
                sh '''
                    docker build -t cicdimage .
                    echo "Docker build complete"
                '''
            }
        }
        stage('Trivy Image Scan') {
    steps {
        sh 'trivy image cicdimage:v1 --format table > trivy-report.txt'
    }
}

stage('Push Docker Image to Docker Hub') {
    steps {
        withCredentials([usernamePassword(
            credentialsId: 'dockercred',
            usernameVariable: 'DOCKER_USER',
            passwordVariable: 'DOCKER_PASS'
        )]) {
            sh '''
                echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                docker tag cicdimage preritsharma/cicdimage
                docker push preritsharma/cicdimage
            '''
        }
    }
}
stage('Deploy to Staging') {
    steps {
        sshagent(['ec2-ssh-key']) {   // 'ec2-ssh-key' = Jenkins SSH credential
            sh """
                echo "🚀 Deploying to Staging EC2: ${EC2_STAGING_IP}"

                ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_STAGING_IP} '

                    # Pull latest image
                    docker pull ${IMAGE_NAME}
                    
                    # Stop old container
                    docker stop 8byte-app || true
                    docker rm 8byte-app   || true

                    # Run new container
                    docker run -d \
                        --name 8byte-app \
                        --restart unless-stopped \
                        -p 8000:8000 \
                        -e DATABASE_URL="${DB_URL}" \
                        ${IMAGE_NAME}
                '
            """
        }
    }
}

stage('Approval') {
            steps {
                // Pause pipeline and wait for input
                timeout(time: 10, unit: 'MINUTES') { // Optional timeout
                    input(
                        message: 'Deploy to Production?',
                        ok: 'Approve',
                    )
                }
            }
        }
        stage('Deploy to PROD') {
    steps {
        sshagent(['ec2-ssh-key']) {   // 'ec2-ssh-key' = Jenkins SSH credential
            sh """
                echo "🚀 Deploying to Staging EC2: ${EC2_PROD_IP}"

                ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_PROD_IP} '

                    # Pull latest image
                    docker pull ${IMAGE_NAME}
                    
                    # Stop old container
                    docker stop 8byte-app || true
                    docker rm 8byte-app   || true

                    # Run new container
                    docker run -d \
                        --name 8byte-app \
                        --restart unless-stopped \
                        -p 8000:8000 \
                        -e DATABASE_URL="${DB_URL}" \
                        ${IMAGE_NAME}
                '
            """
        }
    }
}

}
    
    post {
    always {
        archiveArtifacts artifacts: 'coverage.xml, trivy-report.txt', followSymlinks: false
    }
}
}
