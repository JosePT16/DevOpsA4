// Jenkinsfile (Declarative Pipeline)

// ----- Helper functions -----
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
  /*
    NOTE ABOUT AGENT LABELS:
    - If you do NOT have agent labels set up yet, change all:
        agent { label 'test' } / 'build' / 'deploy'
      to:
        agent any
    - Once you create labels, switch back for grading evidence.
  */
  agent none

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  triggers {
    // Works when webhook is configured; harmless otherwise
    githubPush()
  }

  environment {
    // App / DB
    FLASK_APP = "app:create_app"
    SQLITE_DB_PATH = "staging.db"

    // Artifact versioning
    APP_VERSION = "1.0.${BUILD_NUMBER}"

    // SonarQube (server running locally)
    SONAR_HOST_URL = "http://localhost:9000"

    // k6
    BASE_URL = "http://127.0.0.1:5000"
  }

  stages {

    stage('Checkout') {
      agent { label 'test' }  // change to "agent any" if labels not ready
      steps {
        checkout scm
      }
    }

    stage('Install dependencies') {
      agent { label 'test' }
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
        """.stripIndent())
      }
      post {
        always {
          echo "Tests stage finished"
        }
      }
    }

    stage('Build artifact (ZIP)') {
      agent { label 'build' }
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
              if (Test-Path artifact-${env.APP_VERSION}.zip) { Remove-Item artifact-${env.APP_VERSION}.zip -Force }
              Compress-Archive -Path app, tests, performance, requirements.txt, README.md -DestinationPath artifact-${env.APP_VERSION}.zip -Force
            """.stripIndent())
          }
        }
      }
    }

    stage('SonarQube analysis') {
      agent { label 'test' }
      steps {
        echo "Starting SonarQube analysis..."

        /*
          REQUIREMENTS TO ENABLE THIS STAGE:
          1) Install plugin: "SonarQube Scanner for Jenkins"
          2) Configure SonarQube server in Jenkins:
             Manage Jenkins -> System -> SonarQube servers -> Name: SonarQube
          3) Add credentials (Secret text) with ID: sonarqube-token
          4) Ensure sonar-scanner is available (Jenkins tool config or on PATH)
        */

        withSonarQubeEnv('SonarQube') {
          withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
            script {
              if (isUnix()) {
                runCmd("""
                  sonar-scanner \
                    -Dsonar.host.url=${SONAR_HOST_URL} \
                    -Dsonar.login=${SONAR_TOKEN}
                """.stripIndent())
              } else {
                // Windows PowerShell uses backticks for line continuation
                runCmd("""
                  sonar-scanner `
                    -Dsonar.host.url=${env.SONAR_HOST_URL} `
                    -Dsonar.login=${env.SONAR_TOKEN}
                """.stripIndent())
              }
            }
          }
        }
      }
    }

    stage('Quality Gate') {
      agent { label 'test' }
      steps {
        echo "Waiting for SonarQube Quality Gate..."
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Deploy to staging (local run)') {
      when { expression { return isMainBranch() } }
      agent { label 'deploy' }
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
              Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m","flask","run","--host","127.0.0.1","--port","5000" -RedirectStandardOutput "flask.log" -RedirectStandardError "flask.err.log"
              Start-Sleep -Seconds 2
              Invoke-WebRequest ${env.BASE_URL}/health -UseBasicParsing | Out-Null
            """.stripIndent())
          }
        }
      }
    }

    stage('Performance test (k6)') {
      when { expression { return isMainBranch() } }
      agent { label 'test' }
      steps {
        echo "Running k6 performance test..."
        runCmd("""
          k6 run --summary-export=performance/summary.json performance/load_test.js
        """.stripIndent())
      }
    }

    stage('Archive artifacts') {
      agent { label 'build' }
      steps {
        archiveArtifacts artifacts: "artifact-*.zip, performance/summary.json, flask.log, flask.err.log", fingerprint: true, onlyIfSuccessful: false
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
    always {
      echo "Pipeline finished."
    }
  }
}
