import sys
import os
import regex
import ast
from nltk.stem import PorterStemmer
from nltk import download
download('punkt')


# modify global variables to specify folder paths and stemming option 

# use stemming when preprocessing text
use_stemming = False

# folder where all projects containing bug reports are stored
project_bug_reports_root = "../ExampleProjectData/ProjectBugReports"

# folder to store each projects constructed queries
constructed_queries_root = "../ExampleProjectData/ConstructedQueries"



# read file with backup encoding if utf-8 fails
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
    
    # save files named accordingly
    if use_stemming:
        store_path = store_path + "_stem"
    else:
        store_path = store_path + "_no_stem"
        
    baseline_file_path = os.path.join(store_path, f'{bug_report}_baseline_query_stem.txt')
    extended_file_path = os.path.join(store_path, f'{bug_report}_extended_query_stem.txt')
    os.makedirs(store_path, exist_ok=True)
    
    # save baseline query to file
    with open(baseline_file_path, 'w') as file:
        file.write(baseline_query)
    
    # save extended query to file
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
    
    # iterate through projects
    for project in projects:
        project_path = os.path.join(projects_root, project)
        
        bug_reports = [name for name in os.listdir(project_path) if name.isdigit()]
        bug_reports.sort(key=int)
        
        # iterate through bug reports
        for bug_report in bug_reports:
            bug_report_path = os.path.join(project_path, bug_report)
            store_path = os.path.join(store_root, project)
            preprocess_bug_report(store_path, bug_report_path, bug_report, stopwords, True)
            preprocess_bug_report(store_path, bug_report_path, bug_report, stopwords, False)


if __name__ == "__main__":
    
    main(project_bug_reports_root, constructed_queries_root, use_stemming)
    

