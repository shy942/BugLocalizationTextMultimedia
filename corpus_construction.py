import os
import argparse
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.document import Document, StringField, TextField, Field
from query_construction import preprocess_text, load_stopwords, read_file


# index preprocessed source documents using apache lucene
def index_documents(index_dir, documents):
    lucene.initVM()
    index_path = Paths.get(index_dir)
    store = FSDirectory.open(index_path)
    config = IndexWriterConfig(StandardAnalyzer())
    writer = IndexWriter(store, config)
    
    for filename, content in documents:
        doc = Document()
        doc.add(StringField("filename", filename, Field.Store.YES))
        doc.add(TextField("content", content, Field.Store.YES))
        writer.addDocument(doc)
        print("Added", filename)
    
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
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.startswith('.'):
                file_path = os.path.join(root, file)
                source_documents.append((file, read_file(file_path)))
    return source_documents


def main(source_path, index_path, use_stemming):

    stopwords = load_stopwords("stop_words_english.txt")

    source_documents = collect_source_documents(source_path)
    preprocessed_documents = preprocess_documents(source_documents, stopwords, use_stemming)
    index_documents(index_path, preprocessed_documents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index source documents of a software project using PyLucene.")
    parser.add_argument('project_path', type=str, help='Path to the software project directory')
    parser.add_argument('index_path', type=str, help='Path to the index directory')
    parser.add_argument("--stemming", action="store_true", help="Enable stemming if set")

    args = parser.parse_args()
    main(args.project_path, args.index_path, args.stemming)

