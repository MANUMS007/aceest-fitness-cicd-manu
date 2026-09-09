// ---------------------------------------------------------------------
// Jenkinsfile - ACEest Fitness & Gym
// Handles the "secondary validation layer": Jenkins pulls the latest
// code from GitHub and performs a clean build in a controlled
// environment, independent of GitHub Actions.
// ---------------------------------------------------------------------
pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-fitness"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                git branch: 'main',
                    url: 'https://github.com/MANUMS007/aceest-fitness-cicd-manu.git'
            }
        }

        stage('Set Up Environment') {
            steps {
                echo 'Creating a clean virtual environment...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Build') {
            steps {
                echo 'Compiling application (clean build check)...'
                sh '''
                    . venv/bin/activate
                    python -m py_compile app.py
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    flake8 app.py --max-line-length=100 --extend-ignore=E501
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker image...'
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }
    }

    post {
        success {
            echo 'BUILD stage completed successfully.'
        }
        failure {
            echo 'BUILD stage failed - check console output above.'
        }
    }
}
