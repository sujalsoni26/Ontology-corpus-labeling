# Ontology-corpus-labeling

## Setup Instructions

1. **Install Dependencies**:
   Ensure you have Python 3.7+ installed. Then, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Start the Streamlit app:
   ```bash
   python -m streamlit run app.py
   ```

3. **Access the Application**:
   Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

4. **Login or Signup**:
   - Use the signup tab to create a new account.
   - Login with your credentials to access the labeling tool.

## Features
- User authentication with SQLite and bcrypt.
- Real-time sentence labeling with progress tracking.
- Automatic data synchronization for all users.

## File Descriptions
- `app.py`: Main application file.
- `auth.py`: Handles user authentication.
- `file_store.py`: Manages reading and writing of label data.
- `ui.py`: Contains UI-related customizations.
- `requirements.txt`: Lists all dependencies.
- `users.db`: SQLite database for user credentials.