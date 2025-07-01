import pyodbc
import bcrypt # For password hashing
import speech_recognition as sr
import random

# --- Database Configuration ---
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost\SQLEXPRESS',                
    'database': 'Users',       
    'trusted_connection': 'yes'
}

# --- Language Dictionary ---
LANGUAGE_SPEECH_CODES = {
    "Spanish": "es-ES",
    "French": "fr-FR",
    "Dutch": "nl-NL"
    # Add other languages as needed
}

# --- Speech Recognition Function ---
def get_audio_input(prompt="Speak now...", language_code="en-US"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt)
        r.adjust_for_ambient_noise(source) 
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=10) # Listen for up to 8 seconds, then you have 10 seconds for answer
            print("Processing audio...")
            # Use Google Web Speech API for recognition with the specified language
            text = r.recognize_google(audio, language=language_code)
            print(f"You said: \"{text}\"")
            return text
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return ""
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

class LanguageLesson:
    """
    Represents a single lesson in a language course.
    Contains questions, answers, and manages lesson progress.
    """
    # Modified to accept a language_code parameter
    def __init__(self, name, questions, language_code="en-US"):
        self.name = name
        self.questions = questions  # List of (question_text, correct_answer) tuples
        self.score = 0
        self.current_question_index = 0
        self.language_code = language_code # Store the language code for the lesson

    def start_lesson(self):
        print(f"\n--- Starting Lesson: {self.name} ---")
        self.score = 0
        self.current_question_index = 0
        self._present_next_question()

    def _present_next_question(self):
        if self.current_question_index < len(self.questions):
            question_text, _ = self.questions[self.current_question_index]
            print(f"\nQuestion {self.current_question_index + 1}: {question_text}")

            if self.current_question_index == 2: # on Question 3 you have to answer verbally
                print("Please respond using your voice.")
                user_answer = get_audio_input("Speak your answer now:\n\n ", self.language_code).strip()
            else:
                user_answer = input("Your answer: ").strip()
            # --- END MODIFICATION ---

            self._check_answer(user_answer)
        else:
            self._lesson_complete()

    def _check_answer(self, user_answer):
        _, correct_answer = self.questions[self.current_question_index]
        if user_answer.lower() == correct_answer.lower():
            print("Correct!")
            self.score += 1
        else:
            print(f"Incorrect. The correct answer was: {correct_answer}")

        self.current_question_index += 1
        self._present_next_question() # Move to the next question or finish lesson

    def _lesson_complete(self):
        print(f"\n--- Lesson '{self.name}' Complete! ---")
        print(f"You got {self.score} out of {len(self.questions)} questions correct.")
        print("-------------------------------------")


class DuolingoApp:
    """
    The main Duolingo-like application.
    Manages multiple languages and their respective lessons, and user interaction.
    """



    def __init__(self):
        self.languages = {}
        self.current_user = None # To store the logged-in user's username
        self._initialize_languages_and_lessons()

    def _initialize_languages_and_lessons(self):
        # When initializing lessons, get the language code from the mapping
        # and pass it to the LanguageLesson constructor.

        # --- Spanish Lessons ---
        spanish_lesson1_questions = [
            ("What is 'hello' in Spanish?", "Hola"),
            ("What is 'goodbye' in Spanish?", "Adiós"),
            ("Translate 'thank you' to Spanish.", "Gracias") # This will be the 3rd question (index 2)
        ]
        spanish_lesson1 = LanguageLesson("Spanish Basic Greetings", spanish_lesson1_questions, LANGUAGE_SPEECH_CODES["Spanish"])

        spanish_lesson2_questions = [
            ("What is 'cat' in Spanish?", "Gato"),
            ("What is 'dog' in Spanish?", "Perro"),
            ("Translate 'house' to Spanish.", "Casa") # This will be the 3rd question (index 2)
        ]
        spanish_lesson2 = LanguageLesson("Spanish Common Nouns", spanish_lesson2_questions, LANGUAGE_SPEECH_CODES["Spanish"])

        self.languages["Spanish"] = [spanish_lesson1, spanish_lesson2]

        # --- French Lessons ---
        french_lesson1_questions = [
            ("What is 'hello' in French?", "Bonjour"),
            ("What is 'thank you' in French?", "Merci"),
            ("Translate 'goodbye' to French.", "Au revoir") # This will be the 3rd question (index 2)
        ]
        french_lesson1 = LanguageLesson("French Basic Greetings", french_lesson1_questions, LANGUAGE_SPEECH_CODES["French"])

        french_lesson2_questions = [
            ("What is 'bread' in French?", "Pain"),
            ("What is 'water' in French?", "Eau"),
            ("Translate 'milk' to French.", "Lait") # This will be the 3rd question (index 2)
        ]
        french_lesson2 = LanguageLesson("French Food Items", french_lesson2_questions, LANGUAGE_SPEECH_CODES["French"])

        self.languages["French"] = [french_lesson1, french_lesson2]

        # --- Dutch Lessons ---
        dutch_lesson1_questions = [
            ("What is 'hello' in Dutch?", "Hallo"),
            ("What is 'goodbye' in Dutch?", "Tot ziens"),
            ("Translate 'Can you understand me?' to Dutch.", "Kan jij mij verstaan"), # This is the 3rd question (index 2)
            ("What is 'thank you' in Dutch?", "Dank je wel")
        ]
        dutch_lesson1 = LanguageLesson("Dutch Basic Greetings", dutch_lesson1_questions, LANGUAGE_SPEECH_CODES["Dutch"])

        dutch_lesson2_questions = [
            ("What is 'beer' in Dutch?", "Bier"),
            ("What is 'cheese' in Dutch?", "Kaas"),
            ("Translate 'bike' to Dutch.", "Fiets") # This will be the 3rd question (index 2)
        ]
        dutch_lesson2 = LanguageLesson("Dutch Everyday Nouns", dutch_lesson2_questions, LANGUAGE_SPEECH_CODES["Dutch"])

        self.languages["Dutch"] = [dutch_lesson1, dutch_lesson2]

    def _get_db_connection(self):
        conn_str = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
        )
        if 'trusted_connection' in DB_CONFIG:
            conn_str += f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
        else:
            print("Error: Database connection configuration incomplete.")
            return None

        try:
            conn = pyodbc.connect(conn_str)
            return conn
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            print(f"Database connection error: {sqlstate}")
            print(ex)
            return None

    def _create_user_table_if_not_exists(self):
        conn = self._get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users' AND schema_id = SCHEMA_ID('dbo'))
                    BEGIN
                        CREATE TABLE Users (
                            UserID INT PRIMARY KEY IDENTITY(1,1),
                            Username NVARCHAR(50) UNIQUE NOT NULL,
                            PasswordHash NVARCHAR(255) NOT NULL
                        );
                    END
                """)
                conn.commit()
                print("Users table checked/created successfully.")
            except pyodbc.Error as ex:
                print(f"Error creating Users table: {ex}")
            finally:
                cursor.close()
                conn.close()

    def _register_user(self, username, password):
        conn = self._get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                cursor.execute("INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)",
                               username, hashed_password)
                conn.commit()
                print(f"User '{username}' registered successfully!")
                return True
            except pyodbc.IntegrityError: # For UNIQUE constraint violation (username already exists)
                print(f"Error: Username '{username}' already exists. Please choose a different one.")
                return False
            except pyodbc.Error as ex:
                print(f"Error registering user: {ex}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def _authenticate_user(self, username, password):
        conn = self._get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT PasswordHash FROM Users WHERE Username = ?", username)
                result = cursor.fetchone()
                if result:
                    stored_hash = result[0].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                        print(f"Welcome, {username}!")
                        return True
                    else:
                        print("Invalid password.")
                        return False
                else:
                    print("Username not found.")
                    return False
            except pyodbc.Error as ex:
                print(f"Authentication error: {ex}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def display_auth_menu(self):
        print("\n--- Duolingo Authentication ---")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        print("-------------------------------")

    def display_main_menu(self):
        print(f"\n--- Duolingo Mock App (Logged in as: {self.current_user}) ---")
        print("1. Select a Language")
        print("2. Logout")
        print("-------------------------")

    def run(self):
        self._create_user_table_if_not_exists() # Ensure table exists on startup

        while True:
            if not self.current_user:
                self.display_auth_menu()
                choice = input("Enter your choice: ").strip()

                if choice == '1':
                    username = input("Enter username: ").strip()
                    password = input("Enter password: ").strip()
                    if self._authenticate_user(username, password):
                        self.current_user = username
                    else:
                        print("Login failed.")
                elif choice == '2':
                    username = input("Enter new username: ").strip()
                    password = input("Enter new password: ").strip()
                    if self._register_user(username, password):
                        pass # User registered, can now log in
                    else:
                        print("Registration failed.")
                elif choice == '3':
                    print("Exiting Duolingo Mock App. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
            else:
                # User is logged in, show main app menu
                self.display_main_menu()
                choice = input("Enter your choice: ").strip()

                if choice == '1':
                    self._select_language()
                elif choice == '2':
                    print(f"User '{self.current_user}' logged out.")
                    self.current_user = None # Log out the user
                else:
                    print("Invalid choice. Please try again.")

    def _select_language(self):
        if not self.languages:
            print("No languages available yet. Please add some!")
            return

        print("\nAvailable Languages:")
        language_names = list(self.languages.keys())
        for i, lang_name in enumerate(language_names):
            print(f"{i + 1}. {lang_name}")

        while True:
            try:
                lang_choice_index = int(input("Select a language (enter number): ").strip())
                if 1 <= lang_choice_index <= len(language_names):
                    selected_language_name = language_names[lang_choice_index - 1]
                    self._select_and_start_lesson(selected_language_name)
                    break
                else:
                    print("Invalid language number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def _select_and_start_lesson(self, language_name):
        lessons_for_language = self.languages[language_name]

        if not lessons_for_language:
            print(f"No lessons available for {language_name} yet.")
            return

        print(f"\n--- Lessons for {language_name} ---")
        for i, lesson in enumerate(lessons_for_language):
            print(f"{i + 1}. {lesson.name}")

        while True:
            try:
                lesson_choice = int(input("Select a lesson (enter number): ").strip())
                if 1 <= lesson_choice <= len(lessons_for_language):
                    selected_lesson = lessons_for_language[lesson_choice - 1]
                    selected_lesson.start_lesson()
                    break
                else:
                    print("Invalid lesson number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    app = DuolingoApp()
    app.run()