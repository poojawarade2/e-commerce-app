pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'docker --version'
                sh 'echo Building App'
            }
        }

        stage('Test') {
            steps {
                sh 'echo Running Tests'
            }
        }
    }
}