pipeline {
    agent any

    environment {
        APP_IMAGE = "aceest-fitness:latest"
        PORT = "5000"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Checking out latest source code from GitHub...'
                checkout scm
            }
        }

        stage('Build & Lint') {
            steps {
                echo 'Validating Python syntax and code quality...'
                sh '''
                    python3 -m venv venv || virtualenv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python3 -m py_compile app.py tests/test_app.py
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('Unit Testing') {
            steps {
                echo 'Running Pytest test suite...'
                sh '''
                    . venv/bin/activate
                    pytest -v tests/
                '''
            }
        }

        stage('Docker Image Assembly') {
            steps {
                echo 'Building Docker container image...'
                sh '''
                    docker build -t ${APP_IMAGE} .
                '''
            }
        }

        stage('Containerized Testing') {
            steps {
                echo 'Executing Pytest inside the containerized environment...'
                sh '''
                    docker run --rm ${APP_IMAGE} pytest -v tests/
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed.'
            sh '''
                rm -rf venv || true
            '''
        }
        success {
            echo 'Jenkins BUILD and Quality Gate PASSED successfully!'
        }
        failure {
            echo 'Jenkins BUILD FAILED. Check console logs for errors.'
        }
    }
}
