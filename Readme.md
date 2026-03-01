# Global Tourism Recovery Dashboard

## 📌 Project Overview
This project is an interactive, multi-page web application built with **Plotly Dash**. It is designed for policy analysts and stakeholders to dynamically explore post-pandemic tourism recovery data, simulate future growth scenarios, and manage datasets. 

The application is architected with a strict **Separation of Concerns (SoC)** principle, decoupling pure business logic from the UI presentation layer to ensure high testability and maintainability.

## ⚙️ Features
* **Dashboard**: High-level KPI tracking and overall visitor trends.
* **Market Explorer**: Deep dive into regional performance using interactive Treemaps and Bar charts.
* **Scenario Simulator**: Mathematical forecasting tool decoupled into a pure Python function for deterministic modeling.
* **Data Management**: Interface for uploading and previewing new datasets.

## 🛠️ Prerequisites
Ensure you have the following installed on your system:
* Python 3.9 or higher (Tested on Python 3.12)
* `pip` (Python package installer)

## 🚀 Installation & Setup

**1. Clone or extract the repository**
Navigate to the root directory of the project in your terminal.

**2. Create a virtual environment (Recommended)**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

**3. Install project dependencies**
pip install -e ".[test]"

**4. Install Playwright browsers (Required for E2E Testing)**
playwright install chromium

Running the Application
python app.py