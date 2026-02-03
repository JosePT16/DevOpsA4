// Jenkinsfile (Declarative Pipeline)

def isMainBranch() {
  return env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master'
}

def runCmd(String cmd) {
  if (isUnix()) {
    sh cmd
  } else {
    // Use PowerShell for Windows agents (more reliable than cmd for python/paths)
    powershell cmd
  }
}

pipeline {
  agent none

  options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
  }

  triggers {
    // Works when GitHub webhook is set (Step 7), harmless otherwise.
    githubPush()
  }

  environment {
    // App / DB
    FLASK_APP = "app:create_app"
    SQLITE_DB_PATH = "staging.db"

    // Artifact versioning
    APP_VERSION = "1.0.${BUILD_NUMBER}"

    // SonarQube: configure these in Jenkins Credentials / Global config
    // - SonarQube server name in Jenkins: "SonarQube"
    // - Token credentials ID: "sonarqube-token"
    SONAR_HOST_URL = "http://localhost:9000"

    // k6
    BASE_URL = "http://127.0.0.1:5000"
  }

  stages {

    stage('Checkout') {
      agent { label 'test' }  // <-- Step 7/8: create agents + labels; for now can use "any"
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
          // If you later add junit xml output, archive it here.
          // junit 'test-results/**/*.xml'
        }
      }
    }

    stage('Build artifact (ZIP)') {
      agent { label 'build' } // can be same machine if you want; label helps grading
      steps {
        script {
          if (isUnix()) {
            runCmd("""
              rm -f artifact-${APP_VERSION}.zip || true
              zip -r artifact-${APP_VERSION}.zip app tests performance requirements.txt README.md -x "*.db" -x "**/__pycache__/**" -x "**/.venv/**"
            """.stripIndent())
          } else {
            // Windows: Compress-Archive
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
        // Requires "SonarQube Scanner for Jenkins" plugin + server configured in Jenkins:
        // Manage Jenkins -> System -> SonarQube servers -> Name: SonarQube (match below)
        withSonarQubeEnv('SonarQube') {
          // If you installed "SonarScanner" as a Jenkins tool, you can use:
          // def scannerHome = tool 'SonarScanner'
          // and run "${scannerHome}/bin/sonar-scanner"
          // Here we assume sonar-scanner is available on the agent PATH OR via tool config.
          withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
            runCmd("""
              sonar-scanner ^
                -Dsonar.host.url=${SONAR_HOST_URL} ^
                -Dsonar.login=${SONAR_TOKEN}
            """.stripIndent())
          }
        }
      }
    }

    stage('Quality Gate') {
      agent { label 'test' }
      steps {
        // Requires SonarQube webhook configured in SonarQube -> Administration -> Configuration -> Webhooks
        // URL should be: http(s)://<jenkins-url>/sonarqube-webhook/
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Deploy to staging (local run)') {
      when { expression { return isMainBranch() } }
      agent { label 'deploy' }
      steps {
        script {
          // Minimal "staging" for class: start Flask in background.
          // In real life you'd deploy to a staging server/container.
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
      // Step 10: Notifications (Slack or Email)
      // slackSend channel: '#ci', message: "✅ Build ${env.JOB_NAME} #${env.BUILD_NUMBER} succeeded (${env.BRANCH_NAME})"
      echo "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    failure {
      // slackSend channel: '#ci', message: "❌ Build ${env.JOB_NAME} #${env.BUILD_NUMBER} FAILED (${env.BRANCH_NAME})"
      echo "FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    always {
      // If you started Flask, you can optionally stop it here (Windows harder; keep minimal for now)
      echo "Pipeline finished."
    }
  }
}
