# test the script

from main import Document_indexing
from pathlib import Path
if __name__ == "__main__":


    test_folder = Path("./workspace_test")
 
    # Run the indexer
    app = Document_indexing(test_folder)
    app.build_index()
    
    # Search
    app.search("index")
    app.query("index  data")
    app.search("sqlite")
    # gibrish keystrokes to test
    app.search("nasjkn")
    app.query("gibrish keystrokes jkdnsdjdj")


'''
results =>

Database successfully indexed!
last indexing on: 2026-06-29 17:28:25.229263

Results for 'index':
 -> workspace_test/file_a.txt (Matches: 5)
 -> workspace_test/file_b.txt (Matches: 5)
last indexing on: 2026-06-29 17:28:25.229263

Documents containing ALL words in 'index  data':
 -> workspace_test/file_b.txt
 -> workspace_test/file_a.txt
last indexing on: 2026-06-29 17:28:25.229263

Results for 'sqlite':
 -> workspace_test/file_b.txt (Matches: 1)
last indexing on: 2026-06-29 17:28:25.229263
No records match: 'nasjkn'
last indexing on: 2026-06-29 17:28:25.229263
No document matches all parameters for: 'gibrish keystrokes jkdnsdjdj'
'''
