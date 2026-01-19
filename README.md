# Property Sentence Labeling Interface

A production-ready Streamlit web application for labeling property-specific sentences with multi-user support, database persistence, and advanced word selection features.

## Features

### 🔐 User Authentication
- Simple username-based login system
- Multi-user support with isolated workspaces
- User statistics tracking (total labels, properties labeled)
- Session management with logout functionality

### 🗄️ Database Persistence
- SQLite database for persistent storage
- Automatic save on every label assignment
- User-specific label tracking
- Word selection storage (subject/property/object)
- Ready for Hugging Face Spaces deployment with persistent storage

### 🏷️ Sentence Labeling
- **5 Label Categories**:
  - Full alignment p(D, R) → `pdr`
  - Correct Domain p(D, ?) → `pd`
  - Correct Range p(?, R) → `pr`
  - Incorrect D & R p(?, ?) → `p`
  - No alignment → `n`

### 🎯 Word Selection (Subject/Property/Object)
- Token-based word selection interface
- Click words to mark as Subject, Property, or Object
- Visual highlighting with colored backgrounds:
  - 🔵 Blue for Subject
  - 🟢 Green for Property
  - 🟠 Orange for Object
- Exclusive selection (word can only belong to one category)
- Real-time summary display

### 🧭 Navigation
- Previous/Next sentence navigation
- Jump to previous/next unlabeled sentence
- Auto-scroll to top on navigation
- Progress tracking with percentage completion

### 📊 Statistics & Export
- Real-time progress tracking
- User-specific statistics
- Dataset overview (total properties and sentences)
- JSON export functionality

## Architecture

### File Structure
```
Labeling Interface/
├── app.py                                      # Main Streamlit application
├── components.py                               # Reusable UI components
├── utils.py                                    # Data processing utilities
├── database.py                                 # SQLite database operations
├── requirements.txt                            # Python dependencies
├── test_database.py                           # Database inspection tool
├── property_text_corpus_full_resolved.json   # Input data (11MB)
└── labeling_data.db                           # SQLite database (auto-created)
```

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Labels Table
```sql
CREATE TABLE labels (
    label_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property TEXT NOT NULL,
    sentence TEXT NOT NULL,
    label_code TEXT NOT NULL,
    subject_words TEXT,      -- Comma-separated word indices
    property_words TEXT,     -- Comma-separated word indices
    object_words TEXT,       -- Comma-separated word indices
    labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, property, sentence)
);
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd "Labeling Interface"

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The application will automatically:
- Load data from `property_text_corpus_full_resolved.json`
- Create the SQLite database (`labeling_data.db`)
- Open in your browser at `http://localhost:8501`

## Usage

### 1. Login
- Enter your username
- Your progress is automatically saved and restored

### 2. Select Property
- Choose a property from the dropdown in the main section
- View domain and range information

### 3. Label Sentences
- Read the sentence
- Select a label category (radio buttons)
- Optionally mark words:
  - Click "📘 Subject" button
  - Click words to mark as subject
  - Repeat for Property and Object
- Navigate to next sentence

### 4. Navigation
- **Next/Previous**: Move one sentence at a time
- **Jump to Unlabeled**: Skip to next/previous unlabeled sentence
- Page auto-scrolls to top for easy viewing

### 5. Export
- Click "⬇️ Download Labeled JSON" in sidebar
- Exports your current labeling progress

## Technical Details

### Auto-Save Mechanism
- Labels saved to database on every assignment
- Word selections saved on every click
- No manual save required
- Changes persist across sessions

### Multi-User Support
- Each user has isolated workspace
- User A's labels don't affect User B
- Database tracks labels by `user_id`
- Concurrent usage supported

### Word Selection Storage
Word indices are stored as comma-separated strings:
- Sentence: "The cat sat on the mat"
- Subject: `"1"` → "cat"
- Property: `"2"` → "sat"
- Object: `"5"` → "mat"

### UI/UX Features
- Colored word highlighting (blue/green/orange)
- Auto-scroll to top on navigation
- Real-time progress tracking
- Responsive layout
- Session state management

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Hugging Face Spaces

1. **Create New Space**:
   - Go to https://huggingface.co/new-space
   - Select **Streamlit** as SDK
   - Choose visibility (Public/Private)

2. **Upload Files**:
   - Upload all `.py` files
   - Upload `requirements.txt`
   - Upload `property_text_corpus_full_resolved.json`

3. **Enable Persistent Storage**:
   - Go to Space Settings → Persistent Storage
   - Enable persistent storage (required for database)
   - Database will be stored at `/data/labeling_data.db`

4. **Optional: Add OAuth**:
   Add to Space `README.md`:
   ```yaml
   ---
   title: Sentence Labeler
   sdk: streamlit
   sdk_version: 1.30.0
   hf_oauth: true
   ---
   ```

## Database Inspection

View database contents:
```bash
python3 test_database.py
```

Or use SQLite CLI:
```bash
sqlite3 labeling_data.db
SELECT * FROM users;
SELECT * FROM labels WHERE user_id = 1;
.quit
```

## Technologies Used

- **Streamlit** - Web application framework
- **SQLite** - Lightweight database
- **Python 3** - Backend logic
- **HTML/CSS** - Custom styling for word selection

## Future Enhancements

- [ ] Hugging Face OAuth integration
- [ ] Admin dashboard for user management
- [ ] Inter-annotator agreement metrics
- [ ] Label distribution visualizations
- [ ] Keyboard shortcuts for navigation
- [ ] Multi-word phrase selection
- [ ] Undo/Redo functionality
- [ ] Export to multiple formats (CSV, Excel)

## License

[Add your license here]

## Contributors

[Add contributors here]

## Acknowledgments

Migrated from original Gradio implementation to Streamlit with enhanced features including user authentication, database persistence, and word-level annotation capabilities.
