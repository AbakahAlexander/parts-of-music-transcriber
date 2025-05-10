#!/bin/bash

# Set environment variables (if needed)
if [ -f env_setup.sh ]; then
    source env_setup.sh
fi

# Run the Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
