// Jenkinsfile (Declarative Pipeline)
// DevOps Assignment 4
// This pipeline demonstrates CI/CD with agents, branch logic, artifacts,
// SonarQube analysis, performance testing, and staging deployment.



// QUESTION 3: Jenkins file showing branch specific pipeline logic
def isMainBranch() {
  return env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master'
}

def runCmd(String cmd) {
  if (isUnix()) {
    sh cmd
  } else {
    powershell cmd
  }
}


pipeline {

  
  agent none

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  // QUESTION 3:  GitHub webhook trigger
  triggers {
    githubPush()
  }

  environment {
    // Application configuration
    FLASK_APP = "app:create_app"
    SQLITE_DB_PATH = "staging.db"

    // QUESTION 4: Build and Package
    // Artifact versioning using build number
    APP_VERSION = "1.0.${BUILD_NUMBER}"

    
    // Local SonarQube server
    SONAR_HOST_URL = "http://localhost:9000"

    //Performance Testing
    BASE_URL = "http://127.0.0.1:5000"
  }

  stages {

    stage('Checkout') {
      agent any
      steps {
        checkout scm
      }
    }

    stage('Install dependencies') {
      agent any
      steps {
        runCmd("""
          python --version
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest
        """.stripIndent())
      }
    }

    stage('Run tests (E2E)') {
      
      agent { label 'test' }
      steps {
        runCmd("""
          pytest -q
        """)
      }
    }

    stage('Build artifact (ZIP)') {
      // QUESTION 4: Build and Package
      // Builds and versions application artifacts stored in Jenkins
      agent any
      steps {
        script {
          if (isUnix()) {
            runCmd("""
              rm -f artifact-${APP_VERSION}.zip || true
              zip -r artifact-${APP_VERSION}.zip app tests performance requirements.txt README.md \
                -x "*.db" -x "**/__pycache__/**" -x "**/.venv/**"
            """.stripIndent())
          } else {
            runCmd("""
              if (Test-Path artifact-${env.APP_VERSION}.zip) {
                Remove-Item artifact-${env.APP_VERSION}.zip -Force
              }
              Compress-Archive -Path app, tests, performance, requirements.txt, README.md `
                -DestinationPath artifact-${env.APP_VERSION}.zip -Force
            """.stripIndent())
          }
        }
      }
    }

    stage('SonarQube analysis') {
      
      // Static code analysis using SonarQube
      agent any
      steps {
        echo "Starting SonarQube analysis..."

        withSonarQubeEnv('SonarQube') {
          withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
            script {
              def scannerHome = tool 'SonarScanner'

              if (isUnix()) {
                sh """
                  ${scannerHome}/bin/sonar-scanner \
                    -Dsonar.host.url=${SONAR_HOST_URL} \
                    -Dsonar.token=${SONAR_TOKEN}
                """
              } else {
                powershell """
                  & "${scannerHome}\\bin\\sonar-scanner.bat" `
                    "-Dsonar.host.url=${env.SONAR_HOST_URL}" `
                    "-Dsonar.token=${env.SONAR_TOKEN}"
                """
              }
            }
          }
        }
      }
    }

    stage('Quality Gate') {
      
      // Pipeline will fail if quality gate is not met
      agent any
      steps {
        echo "Waiting for SonarQube Quality Gate..."
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Deploy to staging (local run)') {
      // QUESTION 3: Deployment only happens on main/master branch
      when { expression { return isMainBranch() } }
      agent any
      steps {
        echo "Deploying to staging (local run)..."
        script {
          if (isUnix()) {
            runCmd("""
              nohup flask run --host 0.0.0.0 --port 5000 > flask.log 2>&1 &
              sleep 2
              curl -sSf ${BASE_URL}/health
            """.stripIndent())
          } else {
            runCmd("""
              Start-Process -NoNewWindow -FilePath "python" `
                -ArgumentList "-m","flask","run","--host","127.0.0.1","--port","5000" `
                -RedirectStandardOutput "flask.log" `
                -RedirectStandardError "flask.err.log"
              Start-Sleep -Seconds 2
              Invoke-WebRequest ${env.BASE_URL}/health -UseBasicParsing | Out-Null
            """.stripIndent())
          }
        }
      }
    }

    stage('Performance test (k6)') {
      // Performance Test with k6
      when { expression { return isMainBranch() } }
      agent any
      steps {
        echo "Running k6 performance test..."
        runCmd("""
          k6 run --summary-export=performance/summary.json performance/load_test.js
        """.stripIndent())
      }
    }

    stage('Archive artifacts') {
      agent any
      steps {
        archiveArtifacts artifacts: "artifact-*.zip, performance/summary.json, flask.log, flask.err.log",
                         fingerprint: true,
                         onlyIfSuccessful: false
      }
    }
  }

  post {
    success {
      echo "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${env.BRANCH_NAME})"
    }
    failure {
      echo "FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${env.BRANCH_NAME})"
    }
    always {g
      echo "Pipeline finished."
    }
  }
}
