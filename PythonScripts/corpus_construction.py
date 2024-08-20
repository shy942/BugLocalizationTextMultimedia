import os
import shutil
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.document import Document, StringField, TextField, Field
from query_construction import preprocess_text, load_stopwords, read_file


# modify global variables to specify folder paths and stemming option 

# use stemming when preprocessing text
use_stemming = False

# folder where all projects source codes are contained
soure_codes_root = "../ExampleProjectData/SourceCodes"

# folder to store each projects constructed indexes
project_indexes_root = "../ExampleProjectData/ProjectIndexes"



# index preprocessed source documents using apache lucene
def index_documents(index_dir, documents):

    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)

    index_path = Paths.get(index_dir)
    store = FSDirectory.open(index_path)
    config = IndexWriterConfig(StandardAnalyzer())
    writer = IndexWriter(store, config)
    
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
        preprocessed_content = preprocess_text(content, stopwords, use_stemming)
        preprocessed_docs.append((filename, preprocessed_content))
    return preprocessed_docs


# collect all source documents from a software project
def collect_source_documents(directory):
    source_documents = []
    base_directory = os.path.basename(os.path.normpath(directory))
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if not file.startswith('.'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, os.path.join(directory, ".."))
                source_documents.append((relative_path, read_file(file_path)))
                
    return source_documents


def main(source_root, index_root, use_stemming):

    stopwords = load_stopwords("stop_words_english.txt")
    lucene.initVM()

    for project in os.listdir(source_root):
        source_path = os.path.join(source_root, project, project)
        project_name = next(dir_name for dir_name in os.listdir(source_path) if dir_name != "Corpus")
        project_source_path = os.path.join(source_path, project_name)

        source_documents = collect_source_documents(project_source_path)
        preprocessed_documents = preprocess_documents(source_documents, stopwords, use_stemming)
        
        index_path = os.path.join(index_root, list(project)[-1])
        index_documents(index_path, preprocessed_documents)
        print(f"Indexed {project}")


if __name__ == "__main__":

    main(soure_codes_root, project_indexes_root, use_stemming)


