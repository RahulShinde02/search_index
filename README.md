# Document Indexing Experiment

Search and Indexing  is one of the fundamental teaching for a computer science beginer. This repository is a workspace where I’ve been digging into the mechanics of search systems. Rather than relying on existing tools, I wanted to understand exactly how indexing and retrieval work under the hood by building a system from scratch.

### The Learning Path

My primary objective was to get a hands-on understanding of how unstructured text is transformed into queryable data. This project allowed me to explore:

* **Relational Storage:** Mapping text data into a normalized SQLite schema (`files`, `words`, and `indexes`) to understand how to efficiently store and relate information.
* **Text Processing:** Working through the nuances of cleaning raw text—handling stop words, tokenization, and regex—to ensure accurate retrieval.
* **Retrieval Logic:** Implementing search and intersection queries from the ground up, which gave me a much clearer picture of how search engines handle multiple parameters.

### Current Implementation

The code is a CLI-based exploration of these concepts, enabling me to index local directories and experiment with:

1. **Direct Search:** Retrieving files based on keyword frequency.
2. **Intersection Queries:** Identifying documents that contain *all* terms in a query by leveraging set operations.

### What I’m Exploring Next

As I continue to learn, I’m looking at how to make the system more robust:

* **Incremental Updates:** I want to figure out how to track file modifications so that I only process files that have actually changed.  ✅
* **Ranking Algorithms:** I’m curious about moving beyond simple word counts and into basic relevance ranking  to see how search results can be made more meaningful.

### How to run it

If you are curious about the code, you can clone the repo and run the indexer on your own files:

```bash
# To build the index for a folder
python main.py index

# To find a specific word
python main.py search "keyword"

# To find multiple  word
python main.py query "keyword another keyword"
```
