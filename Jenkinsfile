pipeline {
    agent any

    environment {
        APP_NAME       = "educall-manager"
        IMAGE_NAME     = "rj00/educall_manager"
        IMAGE_TAG      = "${env.BUILD_NUMBER}"
        FULL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"

        KUBE_DEPLOYMENT = "educall-web"
        KUBE_NAMESPACE  = "default"
    }

    stages {

        stage("Checkout") {
            steps {
                git branch: "full_production",
                    url: "https://github.com/Rahul-carpenter/educall_manager.git"
            }
        }

        stage("Build Docker Image") {
            steps {
                sh "docker build -t ${FULL_IMAGE} ."
            }
        }

        stage("Push Image to DockerHub") {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                    sh "docker push ${FULL_IMAGE}"
                }
            }
        }

        stage("Run Tests") {
            steps {
                sh '''
                    python3 -m venv venv

                    # Use POSIX-compatible activation
                    . venv/bin/activate

                    pip install --upgrade pip setuptools wheel --break-system-packages

                    # Avoid building numpy/pandas
                    export PIP_ONLY_BINARY=:all:

                    pip install -r requirements.txt --break-system-packages

                    pytest test.py
                '''
            }
        }


        stage("Deploy to Kubernetes") {
            steps {
                withKubeConfig(credentialsId: 'kubeconfig-credential-id') {

                    sh """
                        kubectl set image deployment/${KUBE_DEPLOYMENT} \
                        web=${FULL_IMAGE} -n ${KUBE_NAMESPACE}

                        kubectl rollout restart deployment/${KUBE_DEPLOYMENT} -n ${KUBE_NAMESPACE}
                        kubectl rollout status deployment/${KUBE_DEPLOYMENT} -n ${KUBE_NAMESPACE}
                    """
                }
            }
        }
    }

    post {
        success { echo "🚀 Deployed successfully!" }
        failure { echo "❌ Deployment Failed!" }
    }
}
