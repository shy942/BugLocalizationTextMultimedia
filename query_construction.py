import argparse
import sys
import os
import regex
import ast
from nltk.stem import PorterStemmer
from nltk import download
download('punkt')



def read_file(file_path, encoding='utf-8'):
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except UnicodeDecodeError:
        # Try a different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            return file.read()


def preprocess_text(text, stopwords, use_stemming):

    # initialize stemmer if needed
    stemmer = PorterStemmer() if use_stemming else None

    # remove urls and the markdown link
    text = regex.sub(r'\!\[.*?\]\(https?://\S+?\)', '', text)
    text = regex.sub(r'https?://\S+|www\.\S+', '', text)
    
    # split camelCase and snake_case while keeping acronyms
    text = regex.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = regex.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    text = text.replace('_', ' ')
    
    # convert to lowercase and split for list comprehensions
    words = text.lower().split()
    
    # remove stopwords 
    words = [word for word in words if word not in stopwords]
    
    # remove whitespace, punctuation, numbers
    text = ' '.join(words)
    text = regex.sub(r"[\s]+|[^\w\s]|[\d]+", " ", text)
    words = text.split()
    
    # remove stopwords again to catch any that were connected to punctuation
    words = [word for word in words if word not in stopwords]
    
    # perform optional stemming
    if use_stemming:
        words = [stemmer.stem(word) for word in words]
        
        # remove any words that became a stop word after stemming
        words = [word for word in words if word not in stopwords]
    
    # remove words with fewer than 3 characters
    words = [word for word in words if len(word) >= 3]
    
    return ' '.join(words)


def preprocess_bug_report(store_path, bug_report_path, bug_report, stopwords, use_stemming):
    
    # gather bug report title and description
    title_path = os.path.join(bug_report_path, 'title.txt')
    description_path = os.path.join(bug_report_path, 'description.txt')
    title = read_file(title_path)
    description = read_file(description_path)
    
    # gather image descriptions and content
    images_info = ""
    files = sorted(os.listdir(bug_report_path))
    for file_name in files:
        if "ImageContent.txt" in file_name:
            file_path = os.path.join(bug_report_path, file_name)
            file_content = read_file(file_path)
            images_info += file_content + "\n"
    
    # preprocessing the bug report text
    baseline_query = preprocess_text(title + " " + description, stopwords, use_stemming)
    extended_query = baseline_query + " " + preprocess_text(images_info, stopwords, use_stemming)
    
    os.makedirs(store_path, exist_ok=True)
    
    # save baseline query to file
    baseline_file_path = os.path.join(store_path, f'{bug_report}_baseline_query.txt')
    with open(baseline_file_path, 'w') as file:
        file.write(baseline_query)
    
    # save extended query to file
    extended_file_path = os.path.join(store_path, f'{bug_report}_extended_query.txt')
    with open(extended_file_path, 'w') as file:
        file.write(extended_query)
        
    print(f"Stored queries for bug report {bug_report} in {store_path}")


# read the stopwords
def load_stopwords(file_path):
    with open(file_path, 'r') as file:
        return set(word.strip() for word in file)


def main(projects_root, store_root, use_stemming):

    stopwords = load_stopwords("stop_words_english.txt")

    projects = [name for name in os.listdir(projects_root) if name.isdigit()]
    projects.sort(key=int)
    
    for project in projects:
        project_path = os.path.join(projects_root, project)
        
        bug_reports = [name for name in os.listdir(project_path) if name.isdigit()]
        bug_reports.sort(key=int)
    
        for bug_report in bug_reports:
            bug_report_path = os.path.join(project_path, bug_report)
            store_path = os.path.join(store_root, project)
            preprocess_bug_report(store_path, bug_report_path, bug_report, stopwords, use_stemming)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text preprocesssing")
    parser.add_argument("process_directory", type=str, help="The directory with projects")
    parser.add_argument("store_directory", type=str, help="The directory to store output query files")
    parser.add_argument("--stemming", action="store_true", help="Enable stemming if set")

    args = parser.parse_args()

    # Call main function with parsed arguments
    main(args.process_directory, args.store_directory, args.stemming)


