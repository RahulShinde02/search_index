import sqlite3
from pypdf import PdfReader
import re
from pathlib import Path
import datetime
from my_stopwords import STOP_WORDS , exclude_dirs , extensions
import argparse
import sys
from collections import deque

folder_path = Path.cwd()


class Document_indexing:
    def __init__(self, directory_path=folder_path):
        self.path = Path(directory_path)
        self.db_dir = self.path / "indexing_files"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.dbname = self.db_dir / "Fileindex.sqlite"
        self.log = self.db_dir /"index.log"
        self._make_db()

    def _make_db(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.dbname) as con:
            cursor = con.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS indexes (
                    word_id INTEGER,
                    file_id INTEGER,
                    freq INTEGER,
                    PRIMARY KEY (word_id, file_id),
                    FOREIGN KEY (word_id) REFERENCES words(word_id),
                    FOREIGN KEY (file_id) REFERENCES files(file_id)
                );
            ''')
            con.commit()
    def _read_pdf(self, filepath):
        """Extract and return text content from a PDF file."""
        text = ""
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            print(f"Error reading PDF {filepath.name}: {e}")
        return text
    
    def _get_last_index_time(self):
        """Read the last timestamp if available from the log and return it as a datetime object else return ancient time"""
        if not self.log.exists():
            return datetime.datetime.min
        with open(self.log, "r") as file:
            ts = deque(file, maxlen=1)
            ts = ts[0].strip()
            try:
                return datetime.datetime.fromisoformat(ts)
            except ValueError:
                return datetime.datetime.min

    def _read_file(self):
        """Read supported files and return a dict mapping paths to content."""
        content_dict = {}
        last_index_time = self._get_last_index_time()
        with sqlite3.connect(self.dbname) as con:
            cursor = con.cursor()
            cursor.execute("SELECT filepath FROM files")
            known_paths = {row[0] for row in cursor.fetchall()}

        for filepath in self.path.rglob("*"):
            if any(part in exclude_dirs for part in filepath.parts):
                continue
            if filepath.is_file() and filepath.suffix.lower() in extensions:
                filepath_posix = filepath.as_posix()

                is_path_new = filepath_posix not in known_paths

                file_mtime = datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
                is_file_edited = file_mtime > last_index_time

                if not is_path_new and not is_file_edited:
                    continue

                if filepath.suffix.lower() == '.pdf':
                    content_dict[filepath_posix] = self._read_pdf(filepath)
                else:
                    try:
                        content_dict[filepath_posix] = filepath.read_text(encoding='utf-8', errors='ignore')
                    except Exception as e:
                        print(f"Error reading {filepath.name}: {e}")
                        
        return content_dict

    def _content_cleaner_indexer(self):
        """Tokenize content, filter stop words, and count word frequencies.
        Returns a dict mapping file paths to a dict of {word: frequency}.
        """
        content_dict = self._read_file()
        clean_dict = {}
        
        for filepath, content in content_dict.items():
            raw_words = re.findall(r'\b\w+\b', content.lower())
            word_counts = {}
            for word in raw_words:
                if word not in STOP_WORDS:
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            clean_dict[filepath] = word_counts
            
        return clean_dict  

    def build_index(self):
        """Parse files, build the inverted index, and save to SQLite."""
        cleaned_data = self._content_cleaner_indexer()
        with sqlite3.connect(self.dbname) as con:
            cursor = con.cursor()
            
            cursor.execute("SELECT word, word_id FROM words")
            word_cache = {row[0]: row[1] for row in cursor.fetchall()}
            
            for filepath, word_counts in cleaned_data.items():
                cursor.execute("INSERT OR IGNORE INTO files (filepath) VALUES (?)", (filepath,))
                cursor.execute("SELECT file_id FROM files WHERE filepath = ?", (filepath,))
                file_id = cursor.fetchone()[0]
                cursor.execute('DELETE FROM indexes WHERE file_id = ?', (file_id,))
                for word, freq in word_counts.items():
                    if word not in word_cache:
                        cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word,))
                        cursor.execute("SELECT word_id FROM words WHERE word = ?", (word,))
                        word_id = cursor.fetchone()[0]
                        word_cache[word] = word_id 
                    else:
                        word_id = word_cache[word]
                                        
                    cursor.execute('''
                        INSERT OR REPLACE INTO indexes (word_id, file_id, freq)
                        VALUES (?, ?, ?)
                    ''', (word_id, file_id, freq))

            con.commit()
        print("Optimising and shrinking database file...")
        with sqlite3.connect(self.dbname) as vacuum_con:
            vacuum_con.execute("VACUUM")
        with open (self.log, "a",encoding='utf-8') as file:
            file.write(f"{datetime.datetime.now()} \n")  

        print("Database successfully indexed!")

    def _Validate(self):
        """Verify that the directory has been indexed."""
        if not self.log.exists():
            print("Directroy Not indexed, please index.")
            sys.exit(1)
        else:
            with open(self.log, "r") as file:
                ts = deque(file, maxlen= 1)
                ts = ts[0].strip()
                print(f"last indexing on: {ts}")

    def search(self, query_word):
        """Search for word frequency across files and print results."""
        self._Validate()
        query_word = query_word.lower().strip()
        
        with sqlite3.connect(self.dbname) as con:
            cursor = con.cursor()
            cursor.execute('''
                SELECT f.filepath, idx.freq 
                FROM indexes idx
                JOIN words w ON idx.word_id = w.word_id
                JOIN files f ON idx.file_id = f.file_id
                WHERE w.word = ?
                ORDER BY idx.freq DESC
            ''', (query_word,))
            results = cursor.fetchall()
            
        if not results:
            print(f"No records match: '{query_word}'")
        else:
            print(f"\nResults for '{query_word}':")
            for path, count in results:
                print(f" -> {path} (Matches: {count})")

    def query(self, user_query):
        """Perform intersection search for multiple words and print results."""
        self._Validate()
        query_words = re.findall(r'\b\w+\b', user_query.lower())

        search_words = [w for w in query_words if w not in STOP_WORDS]
        
        if not search_words:
            print("Query contained only stop words.")
            return

        sets_list = []

        with sqlite3.connect(self.dbname) as con:
            cursor = con.cursor()
            
            for word in search_words:
                cursor.execute('''
                    SELECT f.filepath
                    FROM indexes idx
                    JOIN words w ON idx.word_id = w.word_id
                    JOIN files f ON idx.file_id = f.file_id
                    WHERE w.word = ?
                ''', (word,))
                matching_files = {row[0] for row in cursor.fetchall()}
                sets_list.append(matching_files)
                
        
        if sets_list:
            common = set.intersection(*sets_list)
        else:
            common = set()

        if common:
            print(f"\nDocuments containing ALL words in '{user_query}':")
            for filepath in common:
                print(f" -> {filepath}")
        else:
            print(f"No document matches all parameters for: '{user_query}'")


def main():
    """Execute the CLI interface."""
    parser = argparse.ArgumentParser(description="Document Indexing and Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("index", help="Index documents in the directory")


    search_parser = subparsers.add_parser("search", help="Search for word by freq")
    search_parser.add_argument("search", type=str, help="The search query string")

    search_parser = subparsers.add_parser("query", help="Search for multiple words")
    search_parser.add_argument("query", type=str, help="The search query string")

    args = parser.parse_args()


    indexer = Document_indexing()

    if args.command == "index":
        indexer.build_index()
    elif args.command == "search":
        indexer.search(args.search)
    elif args.command == "query":
        indexer.query(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
