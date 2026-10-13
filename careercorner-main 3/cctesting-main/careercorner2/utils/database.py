import sqlite3
import json
import tempfile
from pathlib import Path
DB_PATH = Path(tempfile.gettempdir()) / "career_corner.db"

def init_database():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            remember_token TEXT
        )
    """)

    # saved_universities table
    c.execute("""
        CREATE TABLE IF NOT EXISTS saved_universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            institution_name TEXT NOT NULL,
            program_name TEXT NOT NULL,
            location TEXT,
            type TEXT,
            grade_required TEXT,
            duration TEXT,
            acceptance_rate TEXT,
            data TEXT NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, institution_name, program_name)
        )
    """)

    # user_quizzes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_quizzes (
            user_id TEXT PRIMARY KEY,
            quiz_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # user_cvs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_cvs (
            user_id TEXT PRIMARY KEY,
            parsed_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # professional_reports table
    c.execute("""
        CREATE TABLE IF NOT EXISTS professional_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            cv_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print("✓ Database initialized with reports table")

# university functions
def save_university(user_id: str, uni_data: dict) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO saved_universities 
            (user_id, institution_name, program_name, location, type, 
             grade_required, duration, acceptance_rate, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, uni_data.get('name', ''), uni_data.get('program_name', ''),
            uni_data.get('location', ''), uni_data.get('type', ''),
            uni_data.get('average_grade_required', 'N/A'), uni_data.get('duration', ''),
            uni_data.get('acceptance_rate', 'N/A'), json.dumps(uni_data)
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error saving university: {e}")
        return False

def get_saved_universities(user_id: str) -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT data, saved_at FROM saved_universities WHERE user_id = ? ORDER BY saved_at DESC', (user_id,))
        results = c.fetchall()
        conn.close()
        universities = []
        for row in results:
            uni_data = json.loads(row[0])
            uni_data['saved_at'] = row[1]
            universities.append(uni_data)
        return universities
    except Exception as e:
        print(f"Error loading saved universities: {e}")
        return []

def remove_saved_university(user_id: str, institution_name: str, program_name: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # deleting from saved_universities table
        c.execute('DELETE FROM saved_universities WHERE user_id = ? AND institution_name = ? AND program_name = ?', 
                 (user_id, institution_name, program_name))
        uni_deleted = c.rowcount > 0
        
        # deleting matching university report from professional_reports
        c.execute("""
            DELETE FROM professional_reports 
            WHERE user_id = ? AND report_type = 'university' 
            AND title LIKE ? AND title LIKE ?
        """, (user_id, f'%{program_name}%', f'%{institution_name}%'))
        report_deleted = c.rowcount > 0
        
        conn.commit()
        conn.close()
        return uni_deleted or report_deleted
    except Exception as e:
        print(f"Error removing university: {e}")
        return False

def is_university_saved(user_id: str, institution_name: str, program_name: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM saved_universities WHERE user_id = ? AND institution_name = ? AND program_name = ?', 
                 (user_id, institution_name, program_name))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking saved status: {e}")
        return False

def get_saved_count(user_id: str) -> int:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM saved_universities WHERE user_id = ?', (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting count: {e}")
        return 0

def clear_all_saved(user_id: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM saved_universities WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing saved universities: {e}")
        return False

# CV functions
def save_user_cv(user_id: str, parsed_data: dict):
    """Save parsed CV data (modern version)"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_cvs (user_id, parsed_data)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                parsed_data = excluded.parsed_data,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, json.dumps(parsed_data)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving CV: {e}")

def load_user_cv(user_id: str):
    """Load user CV data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT parsed_data FROM user_cvs WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None
    except Exception as e:
        print(f"Error loading CV: {e}")
        return None



# reports functions
def save_report(user_id: str, report_type: str, title: str, content: str, cv_data: dict = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        cv_json = json.dumps(cv_data) if cv_data else None
        c.execute("""
            INSERT INTO professional_reports (user_id, report_type, title, content, cv_json)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, report_type, title, content, cv_json))
        report_id = c.lastrowid
        conn.commit()
        conn.close()
        return report_id
    except Exception as e:
        print(f"Error saving report: {e}")
        return None

'''
def load_reports(user_id: str, report_type: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, title, content, cv_json 
            FROM professional_reports 
            WHERE user_id = ? AND report_type = ? 
            ORDER BY created_at DESC
        """, (user_id, report_type))
        reports = []
        for row in c.fetchall():
            cv_data = json.loads(row[3]) if row[3] else {}
            reports.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "cv_data": cv_data
            })
        conn.close()
        return reports
    except Exception as e:
        print(f"Error loading reports: {e}")
        return []
'''

def load_reports(user_id: str, report_type: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if cv_json column exists first (safe upgrade)
        c.execute("PRAGMA table_info(professional_reports)")
        columns = [col[1] for col in c.fetchall()]
        has_cv_json = 'cv_json' in columns
        
        if has_cv_json:
            c.execute("""
                SELECT id, title, content, cv_json
                FROM professional_reports
                WHERE user_id = ? AND report_type = ?
                ORDER BY id DESC
            """, (user_id, report_type))
        else:
            # Fallback if column doesn't exist yet
            c.execute("""
                SELECT id, title, content
                FROM professional_reports
                WHERE user_id = ? AND report_type = ?
                ORDER BY id DESC
            """, (user_id, report_type))
        
        rows = c.fetchall()
        conn.close()
        
        reports = []
        for row in rows:
            report = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
            }
            
            # Only add cv_data if column exists and has value
            if has_cv_json and len(row) > 3 and row[3]:
                try:
                    report["cv_data"] = json.loads(row[3])
                except:
                    report["cv_data"] = None
            else:
                report["cv_data"] = None
            
            reports.append(report)
        
        return reports
        
    except Exception as e:
        print(f"✗ Error loading reports: {e}")
        return []

def delete_report(report_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM professional_reports WHERE id = ?", (report_id,))
        result = c.rowcount > 0
        conn.commit()
        conn.close()
        return result
    except Exception as e:
        print(f"Error deleting report: {e}")
        return False


def save_quiz_result(user_id: str, quiz_data: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO user_quizzes (user_id, quiz_data)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                quiz_data = excluded.quiz_data,
                created_at = CURRENT_TIMESTAMP
        """, (user_id, json.dumps(quiz_data)))
        conn.commit()
        conn.close()
        print(f"✓ Saved quiz for user {user_id}")
        return True
    except Exception as e:
        print(f"✗ Error saving quiz: {e}")
        return False

def load_user_quiz(user_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT quiz_data FROM user_quizzes WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return None
    except Exception as e:
        print(f"✗ Error loading quiz: {e}")
        return None

def load_career_quiz_metadata(user_id: str):
    """Load latest career quiz cv_data (sectors) for Degree Picker"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT cv_json 
            FROM professional_reports 
            WHERE user_id = ? AND report_type = 'career_quiz'
            ORDER BY id DESC 
            LIMIT 1
        """, (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0])
        
        return None
        
    except Exception as e:
        print(f"✗ Error loading career quiz metadata: {e}")
        return None


# initialising on import
if __name__ == "__main__":
    init_database()

init_database()
