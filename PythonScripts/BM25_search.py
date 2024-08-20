import os
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.store import FSDirectory


# modify global variables to specify folder paths

# folder where all projects constructed queries are contained
constructed_queries_root = "../ExampleProjectData/ConstructedQueries"

# folder where all projects constructed indexes are stored
project_indexes_root = "../ExampleProjectData/ProjectIndexes"

# folder to store each projects resulting search results
search_results_root = "../ExampleProjectData/SearchResults"



# write the results to a file
def save_search_results(search_results, project, store_folder):

    if not os.path.exists(store_folder):
        os.makedirs(store_folder)
    
    output_file = os.path.join(store_folder, f"{project}_search_results.txt")
    
    with open(output_file, 'w') as f:
    
        sorted_titles = sorted(search_results.keys())
        
        for title in sorted_titles:
            bug_id, query_type, discard = title.split('_', 2)
            f.write(f"{bug_id},{query_type}\n")
            
            for result in search_results[title]:
                filename = result['filename']
                score = result['score']
                f.write(f"{filename},{score:.4f}\n")
                
    print(f"stored results for project {project} to {output_file}")


def search_index(queries, index_folder):
    
    # Open the index directory
    index_dir = FSDirectory.open(Paths.get(index_folder))
    reader = DirectoryReader.open(index_dir)
    searcher = IndexSearcher(reader)
    searcher.setSimilarity(BM25Similarity())
    analyzer = StandardAnalyzer()

    results = {}

    for query_title, query_str in queries.items():
        
        query = QueryParser("content", analyzer).parse(query_str)
        hits = searcher.search(query, 10).scoreDocs

        result_list = []
        for hit in hits:
            doc = searcher.doc(hit.doc)
            result_list.append({
                'doc_id': hit.doc,
                'filename': doc.get("filename"),
                'content': doc.get("content"),
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


def main(query_root, index_root, store_folder):
    
    lucene.initVM()

    for project in os.listdir(index_root):
        query_folder = os.path.join(query_root, project)
        index_folder = os.path.join(index_root, project)
        
        queries = retrieve_queries(query_folder)
        search_results = search_index(queries, index_folder)
        save_search_results(search_results, project, store_folder)


if __name__ == "__main__":

    main(constructed_queries_root, project_indexes_root, search_results_root)


