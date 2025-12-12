pipeline {

    agent none

    environment {
        IMAGE_NAME     = "rj00/educall_manager"
        IMAGE_TAG      = "${env.BUILD_NUMBER}"
        FULL_IMAGE     = "${IMAGE_NAME}:${IMAGE_TAG}"

        KUBE_DEPLOYMENT = "educall-web"
        KUBE_NAMESPACE  = "default"
    }

    stages {

        stage("Checkout") {
            agent any
            steps {
                git branch: "full_production",
                    url: "https://github.com/Rahul-carpenter/educall_manager.git"
            }
        }

        stage("Run Tests") {
            agent {
                docker {
                    image 'python:3.11'
                    args '-u root:root'
                }
            }
            steps {
                sh """
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pytest -q
                """
            }
        }

        stage("Build Docker Image") {
            agent any
            steps {
                sh "docker build -t ${FULL_IMAGE} ."
            }
        }

        stage("Push Image to DockerHub") {
            agent any
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    usernameVariable: 'DOCKER_PASS'
                )]) {
                    sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                    sh "docker push ${FULL_IMAGE}"
                }
            }
        }

        stage("Deploy to Kubernetes") {
            agent any
            steps {
                withKubeConfig(credentialsId: 'kubeconfig-credential-id') {
                    sh "kubectl set image deployment/${KUBE_DEPLOYMENT} web=${FULL_IMAGE} -n ${KUBE_NAMESPACE}"
                    sh "kubectl rollout restart deployment/${KUBE_DEPLOYMENT} -n ${KUBE_NAMESPACE}"
                    sh "kubectl rollout status deployment/${KUBE_DEPLOYMENT} -n ${KUBE_NAMESPACE}"
                }
            }
        }
    }

    post {
        success { echo "🚀 Deployment successful!" }
        failure { echo "❌ Deployment failed!" }
    }
}
