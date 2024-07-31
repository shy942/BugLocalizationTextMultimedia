import sys
import os
import regex


global_stopwords = set()


def read_file(file_path, encoding='utf-8'):
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except UnicodeDecodeError:
        # Try a different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            return file.read()


def preprocess_text(text):

    # remove urls and the markdown link
    text = regex.sub(r'\!\[.*?\]\(https?://\S+?\)', '', text)
    
    # split camelCase and snake_case while keeping acronyms
    text = regex.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = regex.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    text = text.replace('_', ' ')
    
    # convert to lowercase
    text = text.lower()
    
    # remove stopwords
    words = text.split()
    words = [word for word in words if word not in global_stopwords]
    text = ' '.join(words)
    
    # remove punctuation, numbers
    text = regex.sub(r"[\s]+|[^\w\s]|[\d]+", " ", text)
    
    # remove stop words and words with fewer than 3 characters
    words = text.split()
    words = [word for word in words if word not in global_stopwords and len(word) >= 3]
    return ' '.join(words)


def preprocess_bug_report(bug_report_path, bug_report):
    print(f"Processing bug report {bug_report}")
    
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
    baseline_query = preprocess_text(title + " " + description)
    extended_query = baseline_query + " " + preprocess_text(images_info)
    
    # save baseline query to file
    baseline_file_path = os.path.join(bug_report_path, f'{bug_report}_baseline_query.txt')
    with open(baseline_file_path, 'w') as file:
        file.write(baseline_query)
    
    # save extended query to file
    extended_file_path = os.path.join(bug_report_path, f'{bug_report}_extended_query.txt')
    with open(extended_file_path, 'w') as file:
        file.write(extended_query)


# loop through all bug reports in a project and perform language preprocessing
def preprocess_project(project_path):
    bug_reports = [name for name in os.listdir(project_path) if name.isdigit()]
    bug_reports.sort(key=int)
    for bug_report in bug_reports:
    	bug_report_path = os.path.join(project_path, bug_report)
    	preprocess_bug_report(bug_report_path, bug_report)


# read the stopwords and store them globally
def load_stopwords(file_path):
    global global_stopwords
    with open(file_path, 'r') as file:
        global_stopwords = set(word.strip() for word in file)


def main(projects_root, range_str=None):

    load_stopwords("stop_words_english.txt")

    # process projects in given range
    if range_str:
        start, end = map(int, range_str.split(':'))
        
        for project in range(start, end + 1):
            project_path = os.path.join(projects_root, str(project))
            
            if os.path.exists(project_path) and os.path.isdir(project_path):
                preprocess_project(project_path)
    
    # process all projects
    else:
        projects = [name for name in os.listdir(projects_root) if name.isdigit()]
        projects.sort(key=int)
        for project in projects:
            project_path = os.path.join(projects_root, project)
            preprocess_project(project_path)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 query_construction.py <directory> [range]")
        sys.exit(1)
    
    # Command line arguments
    directory = sys.argv[1]
    range_str = sys.argv[2] if len(sys.argv) == 3 else None

    main(directory, range_str)


