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
    
    bug_reports_affected = []
    bug_reports_missing_groundtruth = []
    
    bug_report_ranks = []
    total_queries = 0
    
    hit_at_k_baseline = {1: 0, 5: 0, 10: 0}
    hit_at_k_extended = {1: 0, 5: 0, 10: 0}
    
    mrr_baseline_sum = 0
    mrr_extended_sum = 0
    
    map_baseline_sum = 0
    map_extended_sum = 0
    print(search_data)
    # iterate over each baseline query, gathering both the baseline and extended queries
    for query, search_results in search_data.items():
    
        query_name, query_type = query
        if query_type != 'baseline':
            continue
        extended_results = search_data[(query_name, 'extended')]
        
        # gather the groundtruth data for comparison against search results
        groundtruth_set, missing_truth_count = groundtruth_data.get(query_name, (set(), 0))
        
        # prevent further calculations if no groundtruth exists
        if not groundtruth_set:
            bug_reports_missing_groundtruth.append(query_name)
            continue
        elif missing_truth_count > 0:
            bug_reports_affected.append(query_name)
        
        # gather the search results for comparison against groundtruth data
        baseline_files = [result.split(',')[0] for result in search_results]
        extended_files = [result.split(',')[0] for result in extended_results]
        
        # compute all baseline and extended ranks
        baseline_ranks = [i + 1 for i, result in enumerate(baseline_files) if result in groundtruth_set]
        extended_ranks = [i + 1 for i, result in enumerate(extended_files) if result in groundtruth_set]

        # Retrieve the first rank if available, otherwise set to None
        baseline_rank = baseline_ranks[0] if baseline_ranks else float('inf')
        extended_rank = extended_ranks[0] if extended_ranks else float('inf')
        
        # store individual ranks (lists of all ranks found)
        bug_report_ranks.append({
            'query_name': query_name,
            'baseline_rank': baseline_ranks if baseline_ranks else None,
            'extended_rank': extended_ranks if extended_ranks else None
        })
        
        # store whether rank improved with the extended query
        if extended_rank < baseline_rank:
            improvement_count += 1
        elif extended_rank == baseline_rank:
            same_count += 1
        else:
            worse_count += 1
        
        # calculate mmr
        if baseline_rank != float('inf'):
            mrr_baseline_sum += 1 / baseline_rank
        if extended_rank != float('inf'):
            mrr_extended_sum += 1 / extended_rank
        
        # Calculate Average Precision (AP) for baseline and extended queries
        def calculate_average_precision(retrieved_files):
            hits = 0
            precision_sum = 0
            for i, file in enumerate(retrieved_files):
                if file in groundtruth_set:
                    hits += 1
                    precision = hits / (i + 1)
                    precision_sum += precision
            return precision_sum / hits if hits > 0 else 0
        
        ap_baseline = calculate_average_precision(baseline_files)
        ap_extended = calculate_average_precision(extended_files)
        
        map_baseline_sum += ap_baseline
        map_extended_sum += ap_extended
        
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
    hit_at_k_baseline_percent = {
        k: (count / total_queries) * 100 if total_queries != 0 else 0 
        for k, count in hit_at_k_baseline.items()
    }
    hit_at_k_extended_percent = {
    k: (count / total_queries) * 100 if total_queries != 0 else 0 
        for k, count in hit_at_k_extended.items()
    }

    
    # Calculate final MRR by dividing the sum by the total number of queries
    mrr_baseline = mrr_baseline_sum / total_queries if total_queries > 0 else 0
    mrr_extended = mrr_extended_sum / total_queries if total_queries > 0 else 0
    
    # Calculate final MAP by dividing the sum by the total number of queries
    map_baseline = (map_baseline_sum / total_queries) * 100 if total_queries > 0 else 0
    map_extended = (map_extended_sum / total_queries) * 100 if total_queries > 0 else 0
    
    return {
        'improvement_count': improvement_count,
        'same_count': same_count,
        'worse_count': worse_count,
        'bug_reports_affected': bug_reports_affected,
        'bug_reports_missing_groundtruth': bug_reports_missing_groundtruth,
        'hit_at_k_baseline_percent': hit_at_k_baseline_percent,
        'hit_at_k_extended_percent': hit_at_k_extended_percent,
        'bug_report_ranks': bug_report_ranks,
        'mrr_baseline': mrr_baseline,
        'mrr_extended': mrr_extended,
        'map_baseline': map_baseline,
        'map_extended': map_extended
    }


# read and format the groundtruth to a dictionary
def parse_groundtruth(groundtruth_file, source_code_root, search_data):

    # these are the only bug reports to consider
    bug_reports = {key[0] for key in search_data.keys()}

    # datasets to keep track of necessary groundtruth data
    groundtruth_data = {}
    all_groundtruth = set()
    missing_groundtruth = set()
    
    with open(groundtruth_file, 'r') as file:
        while True:
            query_line = file.readline().strip()
            
            # exit if end of file
            if not query_line:
                break
                
            # setup for data retrieval
            query_name, num_lines = query_line.split()
            num_lines = int(num_lines)
            groundtruth_entries = set()
            non_existent_count = 0
            
            for _ in range(num_lines):
                line = file.readline().strip()
                
                # skip groundtruth data corresponding to non-existant bug reports
                if not query_name in bug_reports:
                    continue
                    
                # format each path for comparison to search results
                parts = line.split('.')
                if len(parts) > 1:
                    line = os.path.join(*parts[:-1]) + '.' + parts[-1]

                
                # track whether the path actually exists
                full_path = os.path.join(source_code_root, line)
                all_groundtruth.add(full_path)
                if os.path.exists(full_path):
                    groundtruth_entries.add(line)
                else:
                    non_existent_count += 1
                    missing_groundtruth.add(full_path)
            
            # store the formatted data in a dictionary
            if query_name in bug_reports:
                groundtruth_data[query_name] = (groundtruth_entries, non_existent_count)
    
    return groundtruth_data, len(all_groundtruth), len(missing_groundtruth)


# read and format the stored query search results to a dictionary
def parse_search_results(search_result_file):
    search_data = {}
    
    with open(search_result_file, 'r') as file:
        while True:
            query_line = file.readline().strip()
            if not query_line:
                break
            
            query_name, query_type, result_count = query_line.split(',')
            result_count = int(result_count)
            search_results = []
            
            # formatting each path for comparison to groundtruth
            for _ in range(result_count):
                line = file.readline().strip()
                parts = line.split(os.path.sep)
                if len(parts) > 1:
                    line = os.path.join(*parts[1:])
                search_results.append(line)
                
            search_data[(query_name, query_type)] = search_results
            
    return search_data


def main (source_root, results_folder, evaluation_folder):
    
    # iterate over each project that has results computed for it
    for result in os.listdir(results_folder):
    
        # preliminary setup, form strings and ensure everything exists
        parts = result.split('_')
        project = parts[0]
        if parts[-2] == 'no':
            stem_extension = 'no_stem'
        else:
            stem_extension = 'stem'
        
        source_path = os.path.join(source_root, f"Project{project}", f"Project{project}")
        if not os.path.exists(source_path):
            print(f"Couldn't find source code and is skipping project {project}")
            continue
        
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
            print(f"Couldn't process and is skipping project {project}")
            continue
        
        # find the path to the groundtruth file
        groundtruth_file = None
        for file in os.listdir(source_corpus):
            if file.startswith("groundtruth_"):
                groundtruth_file = file
                break
        if not groundtruth_file:
            print("Error: no ground truth file found")
            print(f"Couldn't process and is skipping project {project}")
            continue
            
        print(f"starting project {project}_{stem_extension}")
        
        # gather the search results data
        search_result_path = os.path.join(results_folder, result)
        search_data = parse_search_results(search_result_path)
        
        # gather the groundtruth data
        groundtruth_path = os.path.join(source_corpus, groundtruth_file)
        groundtruth_data, total_groundtruth_count, missing_groundtruth_count = parse_groundtruth(groundtruth_path, source_code_root, search_data)
        
        # compute all query evaluators
        data = compute_evaluation(groundtruth_data, search_data)
        
        # save search results
        bug_reports_considered_count = len(data['bug_report_ranks'])
        bug_reports_missing_count = len(data['bug_reports_missing_groundtruth'])
        bug_report_count = bug_reports_considered_count + bug_reports_missing_count
        
        storage_path = os.path.join(evaluation_folder, f"{project}_query_evaluation_{stem_extension}.txt")
        with open(storage_path, 'w') as file:
            file.write(f"Project {project}:\n\n")
            file.write(f"Total number of groundtruth files: {total_groundtruth_count}\n")
            file.write(f"Total number of bugs: {bug_report_count}\n")
            file.write(f"Total amount of groundtruth files not found in source code: {missing_groundtruth_count}\n")
            
            file.write(f"Total number of Bug reports where all groundtruth files do not exist: {bug_reports_missing_count}\n")
            file.write(f"Bug reports where all groundtruth files do not exist: {data['bug_reports_missing_groundtruth']}\n")
            
            file.write(f"Total number of bug reports where some groundtruth files were missing: {len(data['bug_reports_affected'])}\n")
            file.write(f"Bug reports where some groundtruth files were missing: {data['bug_reports_affected']}\n")
            
            file.write(f"Total number of considered bugs: {bug_reports_considered_count}\n")
            
            file.write(f"\nQE Improved Count: {data['improvement_count']}\n")
            file.write(f"QE Identical Count: {data['same_count']}\n")
            file.write(f"QE Worse Count: {data['worse_count']}\n")
    
            file.write(f"\nHit@K for baseline queries:\n")
            for k, percentage in data['hit_at_k_baseline_percent'].items():
                file.write(f"Hit@{k}: {percentage:.2f}%\n")
        
            file.write(f"\nHit@K for extended queries:\n")
            for k, percentage in data['hit_at_k_extended_percent'].items():
                file.write(f"Hit@{k}: {percentage:.2f}%\n")
                
            file.write(f"\nMRR baseline queries: {data['mrr_baseline']}\n")
            file.write(f"MRR extended queries: {data['mrr_extended']}\n")
            
            file.write(f"\nMAP baseline queries: {data['map_baseline']}\n")
            file.write(f"MAP extended queries: {data['map_extended']}\n")
        
            file.write("\nIndividual Results:\n")
            for rank_info in data['bug_report_ranks']:
                file.write(f"{rank_info['query_name']}, 'Baseline', {rank_info['baseline_rank']}\n")
                file.write(f"{rank_info['query_name']}, 'Extended', {rank_info['extended_rank']}\n")
                
        print(f"stored evaluation for project {project} to {storage_path}")


if __name__ == "__main__":

    main(source_codes_root, search_results_root, evaluation_results_root)


