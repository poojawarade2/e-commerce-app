pipeline {
    agent any

    environment {
        SERVICES = 'product-service order-service cart-service gateway'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'docker --version'
                sh 'docker compose build'
            }
        }

        stage('Test') {
            steps {
                sh 'echo Running Tests'
            }
        }
    }
}
