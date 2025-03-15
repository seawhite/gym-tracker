# Gym Tracker

A simple web application built with Flask to track your workouts at the gym. This application allows you to record exercises, sets, reps, and weights, and visualize your progress over time.

## Features

- Record workout sessions with date and time
- Track exercises, sets, reps, and weights
- Visualize progress with charts and graphs
- Review workout history

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/seawhite/gym-tracker.git
cd gym-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables (optional)

Create a `.env` file in the root directory with the following content:

```
SECRET_KEY=your_secret_key_here
```

If you don't create this file, a default development key will be used.

## Running the Application

```bash
python run.py
```

The application will be available at http://localhost:5000

## Database

The application uses SQLite as the database, which will be automatically created in the `app` directory as `gym_tracker.db` when you first run the application.

## Project Structure

```
gym-tracker/
├── app/                  # Application package
│   ├── __init__.py       # Application factory
│   ├── models.py         # Database models
│   ├── routes.py         # Application routes
│   ├── static/           # Static files (CSS, JS, images)
│   └── templates/        # HTML templates
├── requirements.txt      # Python dependencies
├── run.py               # Application entry point
└── README.md            # This file
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
