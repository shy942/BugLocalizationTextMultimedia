import os
import shutil
import lucene
import re
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.document import Document, StringField, TextField, Field
from query_construction import preprocess_text, load_stopwords, read_file


# modify global variables to specify folder paths

# folder where all projects source codes are contained
source_codes_root = "../ExampleProjectData/SourceCodes"

# folder to store each projects constructed indexes
project_indexes_root = "../ExampleProjectData/ProjectIndexes"



# index preprocessed source documents using apache lucene
def index_documents(index_dir, documents):
    
    # wipe the directory if an old index exists there
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)

    # OOP initializations
    index_path = Paths.get(index_dir)
    store = FSDirectory.open(index_path)
    config = IndexWriterConfig(StandardAnalyzer())
    writer = IndexWriter(store, config)
    
    # index all documents
    for filename, content in documents:
        doc = Document()
        doc.add(StringField("filename", filename, Field.Store.YES))
        doc.add(TextField("content", content, Field.Store.YES))
        writer.addDocument(doc)
    
    writer.close()


# perform natural language preprocessing on each document
def preprocess_documents(documents, stopwords, use_stemming):
    preprocessed_docs = []
    for filename, content in documents:
        print(f"preprocessing {filename}")
        
        try:
            preprocessed_content = preprocess_text(content, stopwords, use_stemming)
            preprocessed_docs.append((filename, preprocessed_content))
            
        except RecursionError:
            print(f"Recursion error processing {filename}. Skipping document.")
            
    return preprocessed_docs


# collect all source documents from a software project
def collect_source_documents(directory):
    source_documents = []
    base_directory = os.path.basename(os.path.normpath(directory))
    for root, dirs, files in os.walk(directory):
    
        # filter out hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if not file.startswith('.'): # filter out hidden files
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, os.path.join(directory, ".."))
                source_documents.append((relative_path, read_file(file_path)))
                
    return source_documents


# get number for project
def extract_number_from_end(string):
    match = re.search(r'(\d+)$', string)
    if match:
        return int(match.group(1))
    else:
        return None


def main(source_root, index_root):

    stopwords = load_stopwords("stop_words_english.txt")
    lucene.initVM()

    # iterate over each project
    for project in os.listdir(source_root):
        
        # find the source code path
        source_path = os.path.join(source_root, project, project)
        project_name = [dir_name for dir_name in os.listdir(source_path)
                   if os.path.isdir(os.path.join(source_path, dir_name))
                   and not dir_name.startswith('.')  # Ignore hidden directories
                   and dir_name != "Corpus"][0]
        project_source_path = os.path.join(source_path, project_name)
        
        
        # gather the source docs and preprocess them
        source_documents = collect_source_documents(project_source_path)
        print(f"starting preprocessing for {project}")
        stem_preprocessed_documents = preprocess_documents(source_documents, stopwords, True)
        no_stem_preprocessed_documents = preprocess_documents(source_documents, stopwords, False)
        print(f"finished preprocessing for {project}")
        
        
        # form paths to store the indexes
        project_num = extract_number_from_end(project)
        stem_index_path = os.path.join(index_root, str(project_num) + "_stem")
        no_stem_index_path = os.path.join(index_root, str(project_num) + "_no_stem")
        
        # index the documents
        index_documents(stem_index_path, stem_preprocessed_documents)
        index_documents(no_stem_index_path, no_stem_preprocessed_documents)
        print(f"Indexed {project}")


if __name__ == "__main__":

    main(source_codes_root, project_indexes_root)


