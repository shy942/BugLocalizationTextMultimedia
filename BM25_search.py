import os
import argparse
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.store import FSDirectory


def search_index(queries, index_folder):

    lucene.initVM()
    
    # Open the index directory
    index_dir = FSDirectory.open(Paths.get(index_folder))
    reader = DirectoryReader.open(index_dir)
    searcher = IndexSearcher(reader)
    searcher.setSimilarity(BM25Similarity())
    analyzer = StandardAnalyzer()

    results = {}

    for query_title, query_str in queries.items():
        print(f"Processing query {query_title}")
        
        query = QueryParser("content", analyzer).parse(query_str)
        hits = searcher.search(query, 3).scoreDocs

        result_list = []
        for hit in hits:
            doc = searcher.doc(hit.doc)
            result_list.append({
                'doc_id': hit.doc,
                'filename': doc.get("filename"),  # Retrieve the filename
                'content': doc.get("content"),    # Retrieve the content
                'score': hit.score
            })

        results[query_title] = result_list

    reader.close()
    index_dir.close()

    return results


def retrieve_queries(query_folder):
    queries = {}
    
    for query_file in os.listdir(query_folder):
        query_file_path = os.path.join(query_folder, query_file)
        
        with open(query_file_path, 'r') as file:
            query_str = file.read().strip()
            
        queries[query_file] = query_str
        
    return queries


def main(query_folder, index_folder):

    queries = retrieve_queries(query_folder)
    search_results = search_index(queries, index_folder)
    
    # temporary print to see search results
    for title, result_list in search_results.items():
        print(f"\nResults for query titled: '{title}'")
        print("=" * 50)
        for idx, result in enumerate(result_list):
            print(f"Result #{idx + 1}:")
            print(f"Document ID: {result['doc_id']}")
            print(f"Filename   : {result['filename']}")
            print(f"Score      : {result['score']:.4f}")
            print("-" * 50)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Search documents using BM25 in PyLucene.")
    parser.add_argument("query_folder", help="Path to the folder containing query files")
    parser.add_argument("index_folder", help="Path to the folder containing the indexed documents")

    args = parser.parse_args()

    main(args.query_folder, args.index_folder)


