# ════════════════════════════════════════════════════
#  ACEest Fitness – Complete Jenkins CI/CD Pipeline
#  Flask REST API version
# ════════════════════════════════════════════════════

pipeline {
    agent any

    environment {
        APP_NAME        = "aceest-fitness"
        VERSION         = "3.2.4"
        DOCKER_HUB_USER = credentials('DOCKER_HUB_USERNAME')
        DOCKER_HUB_PASS = credentials('DOCKER_HUB_PASSWORD')
        DOCKER_IMAGE    = "${DOCKER_HUB_USER}/${APP_NAME}"
        SONAR_HOST_URL  = "http://localhost:9000"
        SONAR_TOKEN     = credentials('SONAR_TOKEN')
        K8S_NAMESPACE   = "aceest"
        BUILD_TAG       = "${VERSION}-${BUILD_NUMBER}"
        PORT            = "5000"
    }

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        // ────────────────────────────────────────────
        stage('Checkout') {
        // ────────────────────────────────────────────
            steps {
                echo "=== Checking out source code ==="
                checkout scm
                script {
                    env.GIT_COMMIT_MSG = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    env.GIT_AUTHOR    = sh(script: 'git log -1 --pretty=%an', returnStdout: true).trim()
                }
                echo "Author : ${env.GIT_AUTHOR}"
                echo "Commit : ${env.GIT_COMMIT_MSG}"
            }
        }

        // ────────────────────────────────────────────
        stage('Setup Python Environment') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // ────────────────────────────────────────────
        stage('Lint & Security') {
        // ────────────────────────────────────────────
            parallel {
                stage('Flake8') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            flake8 app/ --count --max-line-length=127 \
                                   --max-complexity=10 --statistics \
                                   --output-file=flake8-report.txt || true
                            cat flake8-report.txt
                        '''
                    }
                    post { always { archiveArtifacts 'flake8-report.txt' } }
                }
                stage('Pylint') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            pylint app/aceest_app.py --exit-zero \
                                   --output-format=text > pylint-report.txt || true
                            cat pylint-report.txt
                        '''
                    }
                    post { always { archiveArtifacts 'pylint-report.txt' } }
                }
                stage('Bandit Security') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            bandit -r app/ -f txt -o bandit-report.txt || true
                            cat bandit-report.txt
                        '''
                    }
                    post { always { archiveArtifacts 'bandit-report.txt' } }
                }
            }
        }

        // ────────────────────────────────────────────
        stage('Unit Tests & Coverage') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --cov-report=html:coverage-html \
                        --cov-report=term-missing \
                        --cov-fail-under=70 \
                        --html=test-report.html \
                        --self-contained-html
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        reportDir   : 'coverage-html',
                        reportFiles : 'index.html',
                        reportName  : 'Coverage Report',
                        keepAll     : true
                    ])
                    archiveArtifacts artifacts: 'coverage.xml,test-report.html'
                }
                failure { echo "Tests failed — pipeline stopped" }
            }
        }

        // ────────────────────────────────────────────
        stage('SonarQube Analysis') {
        // ────────────────────────────────────────────
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                          -Dsonar.projectKey=aceest-fitness \
                          -Dsonar.projectName="ACEest Fitness" \
                          -Dsonar.projectVersion=${VERSION} \
                          -Dsonar.sources=app \
                          -Dsonar.tests=tests \
                          -Dsonar.python.coverage.reportPaths=coverage.xml \
                          -Dsonar.python.pylint.reportPaths=pylint-report.txt \
                          -Dsonar.host.url=${SONAR_HOST_URL} \
                          -Dsonar.token=${SONAR_TOKEN}
                    '''
                }
            }
        }

        // ────────────────────────────────────────────
        stage('Quality Gate') {
        // ────────────────────────────────────────────
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ────────────────────────────────────────────
        stage('Docker Build') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    docker build \
                        -t ${DOCKER_IMAGE}:${BUILD_TAG} \
                        -t ${DOCKER_IMAGE}:latest .
                    docker images | grep ${APP_NAME}
                '''
            }
        }

        // ────────────────────────────────────────────
        stage('Container Health Verification') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    docker run -d --name ${APP_NAME}-test \
                        -p ${PORT}:5000 \
                        ${DOCKER_IMAGE}:${BUILD_TAG}
                    sleep 8
                    curl --fail http://localhost:${PORT}/health \
                        || (docker logs ${APP_NAME}-test \
                            && docker rm -f ${APP_NAME}-test \
                            && exit 1)
                    docker stop ${APP_NAME}-test
                    docker rm ${APP_NAME}-test
                '''
            }
        }

        // ────────────────────────────────────────────
        stage('Container Security Scan (Trivy)') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    trivy image --exit-code 0 \
                        --severity HIGH,CRITICAL \
                        --format table \
                        --output trivy-report.txt \
                        ${DOCKER_IMAGE}:${BUILD_TAG} || true
                    cat trivy-report.txt
                '''
            }
            post { always { archiveArtifacts 'trivy-report.txt' } }
        }

        // ────────────────────────────────────────────
        stage('Push to Docker Hub') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    echo ${DOCKER_HUB_PASS} | docker login \
                        -u ${DOCKER_HUB_USER} --password-stdin
                    docker push ${DOCKER_IMAGE}:${BUILD_TAG}
                    docker push ${DOCKER_IMAGE}:latest
                    docker logout
                '''
            }
        }

        // ────────────────────────────────────────────
        stage('Deploy to Kubernetes') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    kubectl create namespace ${K8S_NAMESPACE} \
                        --dry-run=client -o yaml | kubectl apply -f -
                    sed -i "s|IMAGE_TAG|${BUILD_TAG}|g" k8s/deployment.yaml
                    sed -i "s|DOCKER_HUB_USER|${DOCKER_HUB_USER}|g" k8s/deployment.yaml
                    kubectl apply -f k8s/ -n ${K8S_NAMESPACE}
                    kubectl rollout status deployment/aceest-deployment \
                        -n ${K8S_NAMESPACE} --timeout=120s
                '''
            }
        }

        // ────────────────────────────────────────────
        stage('Smoke Test') {
        // ────────────────────────────────────────────
            steps {
                sh '''
                    sleep 10
                    SVC_IP=$(kubectl get svc aceest-service \
                        -n ${K8S_NAMESPACE} \
                        -o jsonpath="{.spec.clusterIP}")
                    curl --fail http://${SVC_IP}/health \
                        && echo "Smoke test PASSED"
                '''
            }
        }
    }

    // ── Post actions ─────────────────────────────────
    post {
        success {
            echo "╔══════════════════════════════╗"
            echo "║  PIPELINE SUCCEEDED  ✅       ║"
            echo "╚══════════════════════════════╝"
        }
        failure {
            echo "╔══════════════════════════════╗"
            echo "║  PIPELINE FAILED  ❌          ║"
            echo "╚══════════════════════════════╝"
            sh '''
                kubectl rollout undo deployment/aceest-deployment \
                    -n ${K8S_NAMESPACE} || true
                echo "Auto-rollback triggered"
            '''
        }
        always {
            sh 'docker rmi ${DOCKER_IMAGE}:${BUILD_TAG} || true'
            cleanWs()
        }
    }
}
