import os


# modify global variables to specify folder paths

# folder where all projects source codes are contained
source_codes_root = "../ExampleProjectData/SourceCodes"

# folder where all projects constructed search results are stored
search_results_root = "../ExampleProjectData/SearchResults"

# folder to store each projects evalution of their respective search results
evaluation_results_root = "../ExampleProjectData/EvaluationResults"



# compute all query evaluators
def compute_evaluation(groundtruth_data, search_data):

    improvement_count = 0
    same_count = 0
    worse_count = 0
    
    missing_groundtruth_count = 0
    bug_reports_affected = []
    bug_reports_missing_groundtruth = []
    
    bug_report_ranks = []
    
    hit_at_k_baseline = {1: 0, 5: 0, 10: 0}
    hit_at_k_extended = {1: 0, 5: 0, 10: 0}
    total_queries = 0
    
    # iterate over each baseline query, gathering both the baseline and extended queries
    for query, search_results in search_data.items():
        query_name, query_type = query
        if query_type != 'baseline':
            continue
        
        extended_results = search_data[(query_name, 'extended')]
        
        # gather the search data and groundtruth data for comparison against one another
        groundtruth_set, missing_truth_count = groundtruth_data.get(query_name, (set(), 0))
        baseline_files = [result.split(',')[0] for result in search_results]
        extended_files = [result.split(',')[0] for result in extended_results]
        
        # identify missing groundtruth files
        missing_groundtruth_count += missing_truth_count
        if missing_truth_count > 0:
            bug_reports_affected.append(query_name)
        
        # compute baseline and extended rank
        baseline_rank = next((i + 1 for i, result in enumerate(baseline_files) if result in groundtruth_set), float('inf'))
        extended_rank = next((i + 1 for i, result in enumerate(extended_files) if result in groundtruth_set), float('inf'))
        
        # store individual ranks
        bug_report_ranks.append({
            'query_name': query_name,
            'baseline_rank': baseline_rank if baseline_rank != float('inf') else None,
            'extended_rank': extended_rank if extended_rank != float('inf') else None
        })
        
        # store whether rank improved with the extended query
        if extended_rank < baseline_rank:
            improvement_count += 1
        elif extended_rank == baseline_rank:
            same_count += 1
        else:
            worse_count += 1
        
        # prevent matrices calculations if no groundtruth existed
        if not groundtruth_set:
            bug_reports_missing_groundtruth.append(query_name)
            continue
        
        # Calculate Hit@K for baseline
        for k in hit_at_k_baseline:
            if any(result in groundtruth_set for result in baseline_files[:k]):
                hit_at_k_baseline[k] += 1
        
        # Calculate Hit@K for extended
        for k in hit_at_k_extended:
            if any(result in groundtruth_set for result in extended_files[:k]):
                hit_at_k_extended[k] += 1
        
        total_queries += 1
    
    # compute k percentages
    hit_at_k_baseline_percent = {k: (count / total_queries) * 100 for k, count in hit_at_k_baseline.items()}
    hit_at_k_extended_percent = {k: (count / total_queries) * 100 for k, count in hit_at_k_extended.items()}
    
    return {
        'improvement_count': improvement_count,
        'same_count': same_count,
        'worse_count': worse_count,
        'missing_groundtruth_count': missing_groundtruth_count,
        'bug_reports_affected': bug_reports_affected,
        'bug_reports_missing_groundtruth': bug_reports_missing_groundtruth,
        'hit_at_k_baseline_percent': hit_at_k_baseline_percent,
        'hit_at_k_extended_percent': hit_at_k_extended_percent,
        'bug_report_ranks': bug_report_ranks
    }


# read and format the groundtruth to a dictionary
def parse_groundtruth(groundtruth_file, source_code_root):
    groundtruth_data = {}
    
    with open(groundtruth_file, 'r') as file:
        while True:
            query_line = file.readline().strip()
            if not query_line:
                break
            query_name, num_lines = query_line.split()
            num_lines = int(num_lines)
            groundtruth_entries = set()
            non_existent_count = 0
            
            for _ in range(num_lines):
                line = file.readline().strip()
                parts = line.split('.')
                if len(parts) > 1:
                    line = '/'.join(parts[:-1]) + '.' + parts[-1]
                
                full_path = os.path.join(source_code_root, line)
                if os.path.exists(full_path):
                    groundtruth_entries.add(line)
                else:
                    non_existent_count += 1
                
            groundtruth_data[query_name] = (groundtruth_entries, non_existent_count)
        
    return groundtruth_data


# read and format the stored query search results to a dictionary
def parse_search_results(search_result_file):
    search_data = {}
    with open(search_result_file, 'r') as file:
        while True:
            query_line = file.readline().strip()
            if not query_line:
                break
            query_name, query_type = query_line.split(',')
            search_results = []
            for _ in range(10):
                line = file.readline().strip()
                parts = line.split('/')
                if len(parts) > 1:
                    line = '/'.join(parts[1:])
                search_results.append(line)
            search_data[(query_name, query_type)] = search_results
    return search_data


def main (source_root, results_folder, evaluation_folder):
    
    # iterate over each project that has results computed for it
    for result in os.listdir(results_folder):
    
        project = list(result)[0]
        source_path = os.path.join(source_root, f"Project{project}", f"Project{project}")
        
        # find the path to the source code
        source_corpus = None
        source_code_root = None
        for file in os.listdir(source_path):
            if file.startswith("Corpus"):
                source_corpus = os.path.join(source_path, file)
            elif not file.startswith("."):
                source_code_root = os.path.join(source_path, file)
        if not source_corpus or not source_code_root:
            print(f"Error with groundtruth location:{source_corpus} or source code location:{source_code_root}")
            exit(1)
        
        # find the path to the groundtruth file
        groundtruth_file = None
        for file in os.listdir(source_corpus):
            if file.startswith("groundtruth_"):
                groundtruth_file = file
                break
        if not groundtruth_file:
            print("Error no ground truth file found")
            exit(1)
        
        # gather the groundtruth data
        groundtruth_path = os.path.join(source_corpus, groundtruth_file)
        groundtruth_data = parse_groundtruth(groundtruth_path, source_code_root)
        
        # gather the search results data
        search_result_path = os.path.join(results_folder, result)
        search_data = parse_search_results(search_result_path)
        
        # compute all query evaluators
        data = compute_evaluation(groundtruth_data, search_data)
        
        # save search results
        storage_path = os.path.join(evaluation_folder, f"{project}_query_evaluation.txt")
    with open(storage_path, 'w') as file:
        file.write(f"Total amount of groundtruth files not found in source code: {data['missing_groundtruth_count']}\n")
        file.write(f"Bug reports where all groundtruth files do not exist: {data['bug_reports_missing_groundtruth']}\n")
        file.write(f"Bug reports where some groundtruth files were missing: {data['bug_reports_affected']}\n")
        file.write(f"\nQE Improved Count: {data['improvement_count']}\n")
        file.write(f"QE Identical Count: {data['same_count']}\n")
        file.write(f"QE Worse Count: {data['worse_count']}\n")
    
        file.write(f"\nHit@K for baseline queries:\n")
        for k, percentage in data['hit_at_k_baseline_percent'].items():
            file.write(f"Hit@{k}: {percentage:.2f}%\n")
        
        file.write(f"\nHit@K for extended queries:\n")
        for k, percentage in data['hit_at_k_extended_percent'].items():
            file.write(f"Hit@{k}: {percentage:.2f}%\n")
        
        file.write("\nQuery Ranks:\n")
        for rank_info in data['bug_report_ranks']:
            file.write(f"{rank_info['query_name']}, 'Baseline', {rank_info['baseline_rank']}\n")
            file.write(f"{rank_info['query_name']}, 'Extended', {rank_info['extended_rank']}\n")
                
        print(f"stored evaluation for project {project} to {storage_path}")


if __name__ == "__main__":

    main(source_codes_root, search_results_root, evaluation_results_root)


