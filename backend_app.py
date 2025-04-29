# backend_app.py
import flask
import csv
import os
import datetime
import json

# --- Configuration ---
# PythonAnywhere specific: Use absolute paths in your PythonAnywhere file storage
username = os.environ.get('USER', 'your_pythonanywhere_username') # Fallback needed if USER isn't set

# Directory for data files
DATA_DIR = f'/home/{username}/calculator_data' # Store data in a subfolder

# File for evaluation data
EVAL_DATA_FILE = os.path.join(DATA_DIR, 'calculator_data.csv')
EVAL_CSV_HEADER = [
    'researchId', 'timestamp', 'age', 'sex', 'renalInputMethod',
    'serumCreatinine', 'eGFR', 'renalStatus', 'fallsHistory',
    'knownMedicationsJson', 'otherMedicationsJson', 'totalACB',
    'beersAlertsCount', 'stoppAlertsCount'
]

# File for suggestion data
SUGGESTIONS_FILE = os.path.join(DATA_DIR, 'suggestions.csv')
SUGGESTIONS_HEADER = ['timestamp', 'medicationName', 'details', 'email']

# --- Flask App Initialization ---
app = flask.Flask(__name__)

# --- Helper Functions ---
def initialize_csv(file_path, header):
    """Creates the directory and CSV file with a header if they don't exist."""
    try:
        # Create the directory if it doesn't exist
        dir_name = os.path.dirname(file_path)
        if dir_name: # Ensure directory name is not empty
             os.makedirs(dir_name, exist_ok=True)

        # Check if the file needs initialization
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            print(f"Initialized data file: {file_path}")
    except OSError as e:
        print(f"Error creating directory or initializing CSV file '{file_path}': {e}")
        # Log this error, but the app might still function partially

# --- API Endpoints ---

@app.route('/save_data', methods=['POST'])
def save_data():
    """
    Receives patient and evaluation data via POST request (JSON)
    and appends it to the EVAL_DATA_FILE CSV.
    """
    # Ensure the directory and CSV file exist
    initialize_csv(EVAL_DATA_FILE, EVAL_CSV_HEADER)

    if not flask.request.is_json:
        print("Request received is not JSON")
        return flask.jsonify({"error": "Request must be JSON"}), 400

    data = flask.request.get_json()
    print(f"Received data for /save_data: {json.dumps(data)}")

    try:
        row_data = {
            'researchId': data.get('researchId', f'MISSING_ID_{datetime.datetime.now().isoformat()}'),
            'timestamp': data.get('timestamp', datetime.datetime.now().isoformat()),
            'age': data.get('age'),
            'sex': data.get('sex'),
            'renalInputMethod': data.get('renalInputMethod'),
            'serumCreatinine': data.get('serumCreatinine'),
            'eGFR': data.get('eGFR'),
            'renalStatus': data.get('renalStatus'),
            'fallsHistory': data.get('fallsHistory'),
            'knownMedicationsJson': json.dumps(data.get('knownMedications', [])),
            'otherMedicationsJson': json.dumps(data.get('otherMedications', [])),
            'totalACB': data.get('results', {}).get('totalACB'),
            'beersAlertsCount': data.get('results', {}).get('beersAlerts'),
            'stoppAlertsCount': data.get('results', {}).get('stoppAlerts')
        }
        final_row = {key: row_data.get(key) for key in EVAL_CSV_HEADER}

    except Exception as e:
        print(f"Error processing received /save_data data: {e}")
        return flask.jsonify({"error": "Invalid data format"}), 400

    try:
        if not os.path.exists(EVAL_DATA_FILE):
             print(f"Error: Data file {EVAL_DATA_FILE} could not be created or found.")
             return flask.jsonify({"error": "Could not access data storage"}), 500

        with open(EVAL_DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=EVAL_CSV_HEADER)
            writer.writerow(final_row)

        print(f"Evaluation data saved successfully for ID: {final_row['researchId']}")
        return flask.jsonify({"message": "Evaluation data saved successfully"}), 200

    except IOError as e:
        print(f"Error writing to CSV file '{EVAL_DATA_FILE}': {e}")
        return flask.jsonify({"error": "Could not save evaluation data due to file error"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during file writing: {e}")
        return flask.jsonify({"error": "An internal server error occurred"}), 500


@app.route('/save_suggestion', methods=['POST'])
def save_suggestion():
    """
    Receives suggestion data via POST request (JSON)
    and appends it to the SUGGESTIONS_FILE CSV.
    """
    # Ensure the directory and CSV file exist
    initialize_csv(SUGGESTIONS_FILE, SUGGESTIONS_HEADER)

    if not flask.request.is_json:
        print("Suggestion request received is not JSON")
        return flask.jsonify({"error": "Request must be JSON"}), 400

    data = flask.request.get_json()
    print(f"Received data for /save_suggestion: {json.dumps(data)}")

    try:
        # Validate required fields
        med_name = data.get('medicationName')
        details = data.get('details')
        if not med_name or not details:
            raise ValueError("Missing required suggestion fields (medicationName or details)")

        # Prepare row data
        row_data = {
            'timestamp': data.get('timestamp', datetime.datetime.now().isoformat()),
            'medicationName': med_name,
            'details': details,
            'email': data.get('email') # Optional field
        }
        # Ensure all header keys are present
        final_row = {key: row_data.get(key) for key in SUGGESTIONS_HEADER}

    except ValueError as ve:
         print(f"Validation error for suggestion: {ve}")
         return flask.jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error processing received /save_suggestion data: {e}")
        return flask.jsonify({"error": "Invalid suggestion data format"}), 400

    # --- Append Data to CSV ---
    try:
        if not os.path.exists(SUGGESTIONS_FILE):
             print(f"Error: Suggestions file {SUGGESTIONS_FILE} could not be created or found.")
             return flask.jsonify({"error": "Could not access suggestion storage"}), 500

        with open(SUGGESTIONS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SUGGESTIONS_HEADER)
            writer.writerow(final_row)

        print(f"Suggestion saved successfully for: {final_row['medicationName']}")
        return flask.jsonify({"message": "Suggestion saved successfully"}), 200

    except IOError as e:
        print(f"Error writing to CSV file '{SUGGESTIONS_FILE}': {e}")
        return flask.jsonify({"error": "Could not save suggestion due to file error"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during suggestion file writing: {e}")
        return flask.jsonify({"error": "An internal server error occurred"}), 500


# --- Run the App (for local testing, PythonAnywhere uses WSGI config) ---
if __name__ == '__main__':
    print(f"Starting Flask server for local testing.")
    # Initialize both files for local testing
    initialize_csv(EVAL_DATA_FILE, EVAL_CSV_HEADER)
    initialize_csv(SUGGESTIONS_FILE, SUGGESTIONS_HEADER)
    print(f"Local eval data file: {EVAL_DATA_FILE}")
    print(f"Local suggestions file: {SUGGESTIONS_FILE}")
    app.run(debug=True, host='0.0.0.0', port=5001) # Use a different port like 5001 for local test
