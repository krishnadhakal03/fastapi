pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
    }

    stages {
        stage('Setup Python') {
            steps {
                bat '''
                    python -m venv venv
                    venv\\Scripts\\pip install --upgrade pip
                    venv\\Scripts\\pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat '''
                    set PYTHONPATH=%cd%
                    venv\\Scripts\\pytest tests/ --cov=app --cov-report=term-missing
                '''
            }
        }

        stage('Run FastAPI App') {
            steps {
                bat '''
                    venv\\Scripts\\uvicorn app.main:app --host 0.0.0.0 --port 8000
                '''
            }
        }
    }
}
