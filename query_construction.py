import sys
import os
import regex
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')


def preprocess_text(text):

    # remove urls
    text = regex.sub(r'https?://\S+|www\.\S+', '', text)
    
    # split camelCase while keeping acronyms
    text = regex.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = regex.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    
    # remove underscores, punctuation, numbers
    text = regex.sub(r"_|[\s]+|[^\w\s]|[\d]+", " ", text)
    
    # split into words and remove stopwords
    words = text.split()
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.lower() not in stop_words]

    return ' '.join(filtered_words)


def preprocess_bug_report(bug_report_path, bug_report):
    print(f"Processing bug report {bug_report}")
    
    # gather bug report title and description
    title_path = os.path.join(bug_report_path, 'title.txt')
    description_path = os.path.join(bug_report_path, 'description.txt')
    with open(title_path, 'r') as file:
        title = file.read()
    with open(description_path, 'r') as file:
        description = file.read()
    
    # gather image descriptions and content
    images_info = ""
    files = sorted(os.listdir(bug_report_path))
    for file_name in files:
        if "ImageDescription.txt" in file_name or "ImageContent.txt" in file_name:
            file_path = os.path.join(bug_report_path, file_name)
            with open(file_path, 'r') as file:
                file_content = file.read()
                images_info += file_content + "\n"
    
    # preprocessing the bug report text
    baseline_query = preprocess_text(title + "\n" + description)
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


def main(projects_root, range_str=None):

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

