# DevOps Assignment 3 – CI Pipeline with Jenkins

This project is a simple web application built with Python Flask and SQLite, designed to demonstrate the implementation of a Continuous Integration (CI) pipeline using Jenkins. The pipeline enforces code quality standards, runs automated tests with coverage requirements, and generates build artifacts.

The application shows a list of dishes from a preset database. It have 5 endpoints for:
- Showing the application
- Testing the health
- Retrieve stored dishes (in json)
- Add a new dish
- Delete a dish


SQLite is used as the database for simplicity and portability.


---

## Project Structure

```text

│   .flake8
│   app.db
│   Jenkinsfile
│   pyproject.toml
│   README.md
│   requirements-dev.txt
│   requirements.txt
│
├───app
│   │   db.py
│   │   init.sql
│   │   routes.py
│   │   __init__.py

└───tests
    │   conftest.py
    │   test_dishes.py
    │   test_health.py

```

## Requirements

- Python 3.12+
- pip

---

## Local Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

#For insaling the requirements
pip install -r requirements.txt -r requirements-dev.txt

#For initialize the database
sqlite3 ci.db < app/init.sql
flask --app app run

#The web application will be availabe in
http://127.0.0.1:5000

#For running the test
python -m pytest --cov=app --cov-report=term-missing
```

## CI Pipeline (Jenkins)

The project includes a Jenkinsfile that defines a complete CI pipeline with the following stages:

1. Checkout

- Pulls source code from the GitHub repository

2. Environment Setup

- Creates an isolated Python virtual environment
- Installs runtime and development dependencies
- Configures required environment variables

3. Code Quality Checks
- Black is used to enforce code formatting
- flake8 is used for linting and static analysis
- The pipeline fails if formatting or linting standards are not met

4. Testing and Coverage

- Runs unit tests using pytest
- Enforces a minimum coverage threshold of 80%
- Generates coverage reports in XML and HTML formats

5. Build

- Builds Python distribution artifacts 
- Archives build outputs as Jenkins artifacts
- Executed only on the main branch


## CI Triggers

The Jenkins pipeline is configured using a Multibranch Pipeline and runs automatically when:

Code is pushed to the main branch

A pull request is opened or updated targeting main

Conditional execution is used to avoid unnecessary builds, ensuring that artifact generation only occurs on the main branch.
