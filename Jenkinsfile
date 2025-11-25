pipeline {
    agent any

    environment {
        SONARQUBE = 'sonarqube'
        SCANNER = 'sonar-scanner'
        SONAR_PROJECT_KEY = 'vampyr-backend-rag'
        PYTHON_VERSION = '3.12.10'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/EJJGA-Soft/BACKEND_RAG_VAMPYR'
                    ]]
                ])
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3.12 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest --cov=. --cov-report=xml --cov-report=html || true
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv("${SONARQUBE}") {
                        sh """
                            ${tool SCANNER}/bin/sonar-scanner \
                                -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                -Dsonar.sources=. \
                                -Dsonar.python.version=${PYTHON_VERSION} \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.host.url=http://74.208.227.171:9000 \
                                -Dsonar.login=${SONAR_TOKEN}
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Deploy to Server') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'deploy-server-credentials',
                            usernameVariable: 'SSH_USER',
                            passwordVariable: 'SSH_PASS'
                        ),
                        string(credentialsId: 'deploy-server-host', variable: 'DEPLOY_HOST')
                    ]) {
                        sh '''
                            sshpass -p "${SSH_PASS}" ssh -o StrictHostKeyChecking=no ${SSH_USER}@${DEPLOY_HOST} << 'ENDSSH'
                                cd /home/VAMPYR/BACKEND_RAG_VAMPYR/
                                git pull origin main
                                cd ..

                                docker-compose down  
                                docker-compose up --build -d
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finalizado.'
        }
        success {
            echo 'Pipeline completado correctamente.'
        }
        failure {
            echo 'Pipeline falló.'
        }
    }
}
