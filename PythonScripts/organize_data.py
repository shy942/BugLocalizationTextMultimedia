import os
import re
import ast


# modify global variables to specify folder paths

# folder where all evaluation results files are located
evaluation_results_root = "../ExampleProjectData/EvaluationResults"

# folder to store organized data output
organized_data_root = "../ExampleProjectData/OrganizedData"



# function to organize and write gathered results to files
def write_results_all(data, organized_data_root, postfix):
    data = sorted(data, key=lambda x: x['project'])
    file_name = os.path.join(organized_data_root, f"AllRank_Information{postfix}")

    # Open the file in write mode
    with open(file_name, 'w') as file:

        # Write the header
        file.write("ProjectID,BugID,Technique,Ranks\n")
        
        # Iterate through each sorted project data and write it to the file
        for result in data:
            project = result['project']
            for bug_id, technique, ranks in result['individual_results']:

                file.write(f"{project},{bug_id},{technique},{ranks}\n")


# function to organize and write gathered hit@k data to files
def write_results_hitk(data, organized_data_root, postfix):
    data = sorted(data, key=lambda x: x['project'])
    file_name = os.path.join(organized_data_root, f"HitK_Information{postfix}")

    # Initialize counters and sums for the average calculation
    total_projects = 0
    hit1_baseline_sum = 0.0
    hit5_baseline_sum = 0.0
    hit10_baseline_sum = 0.0
    hit1_extended_sum = 0.0
    hit5_extended_sum = 0.0
    hit10_extended_sum = 0.0

    # Open the file in write mode
    with open(file_name, 'w') as file:

        # header
        file.write("ProjectID,Hit@1_baseline,Hit@5_baseline,Hit@10_baseline,Hit@1_extended,Hit@5_extended,Hit@10_extended\n")
        
        # Iterate through each sorted project data and write it to the file
        for result in data:

            # Extract relevant fields
            project = result['project']
            hit1_baseline = result['hit_at_k_baseline']['hit@1']
            hit5_baseline = result['hit_at_k_baseline']['hit@5']
            hit10_baseline = result['hit_at_k_baseline']['hit@10']
            hit1_extended = result['hit_at_k_extended']['hit@1']
            hit5_extended = result['hit_at_k_extended']['hit@5']
            hit10_extended = result['hit_at_k_extended']['hit@10']
            
            # Write the data line
            file.write(f"{project},{hit1_baseline},{hit5_baseline},{hit10_baseline},{hit1_extended},{hit5_extended},{hit10_extended}\n")
            
            # Update the counters and sums
            total_projects += 1
            hit1_baseline_sum += hit1_baseline
            hit5_baseline_sum += hit5_baseline
            hit10_baseline_sum += hit10_baseline
            hit1_extended_sum += hit1_extended
            hit5_extended_sum += hit5_extended
            hit10_extended_sum += hit10_extended
        
        # Calculate averages
        if total_projects > 0:
            hit1_baseline_avg = hit1_baseline_sum / total_projects
            hit5_baseline_avg = hit5_baseline_sum / total_projects
            hit10_baseline_avg = hit10_baseline_sum / total_projects
            hit1_extended_avg = hit1_extended_sum / total_projects
            hit5_extended_avg = hit5_extended_sum / total_projects
            hit10_extended_avg = hit10_extended_sum / total_projects
        else:
            hit1_baseline_avg = hit5_baseline_avg = hit10_baseline_avg = 0
            hit1_extended_avg = hit5_extended_avg = hit10_extended_avg = 0
        
        # Write the summary line with averages
        file.write(f"Average,{hit1_baseline_avg},{hit5_baseline_avg},{hit10_baseline_avg},{hit1_extended_avg},{hit5_extended_avg},{hit10_extended_avg}\n")


# function to organize and write gathered QE data to files
def write_results_QE(data, organized_data_root, postfix):
    data = sorted(data, key=lambda x: x['project'])
    file_name = os.path.join(organized_data_root, f"AllQE_information{postfix}")
    
    # Initialize counters for the summary line
    total_projects = 0
    total_bugs_sum = 0
    total_considered_bugs_sum = 0
    total_groundtruth_files_sum = 0
    qe_improved_count_sum = 0
    qe_identical_count_sum = 0
    qe_worse_count_sum = 0

    # Open the file in write mode
    with open(file_name, 'w') as file:

        # header
        file.write("ProjectID,TotalBugs,ConsideredBugs,GroundtruthFiles,QE_Improvement,QE_Preserved,QE_Worsened\n")
        
        # Iterate through each project data and write it to the file
        for result in data:

            # Extract relevant fields
            project = result['project']
            total_bugs = result['total_bugs']
            total_considered_bugs = result['total_considered_bugs']
            total_groundtruth_files = result['total_groundtruth_files']
            qe_improved_count = result['qe_improved_count']
            qe_identical_count = result['qe_identical_count']
            qe_worse_count = result['qe_worse_count']
            
            # Write the data line
            file.write(f"{project},{total_bugs},{total_considered_bugs},{total_groundtruth_files},{qe_improved_count},{qe_identical_count},{qe_worse_count}\n")

            # Update the counters
            total_projects += 1
            total_bugs_sum += total_bugs
            total_considered_bugs_sum += total_considered_bugs
            total_groundtruth_files_sum += total_groundtruth_files
            qe_improved_count_sum += qe_improved_count
            qe_identical_count_sum += qe_identical_count
            qe_worse_count_sum += qe_worse_count

        # Write the summary line
        file.write(f"{total_projects},{total_bugs_sum},{total_considered_bugs_sum},{total_groundtruth_files_sum},{qe_improved_count_sum},{qe_identical_count_sum},{qe_worse_count_sum}\n")


# function to retrieve all data from an evaluation results file
def extract_data_from_file(file_path):

    # initialize where data will be stored
    data = {
        'project': None,
        'total_groundtruth_files': 0,
        'total_bugs': 0,
        'total_groundtruth_not_found': 0,
        'total_bug_reports_no_groundtruth': 0,
        'bug_reports_no_groundtruth': [],
        'total_bug_reports_missing_groundtruth': 0,
        'bug_reports_missing_groundtruth': [],
        'total_considered_bugs': 0,
        'qe_improved_count': 0,
        'qe_identical_count': 0,
        'qe_worse_count': 0,
        'hit_at_k_baseline': {},
        'hit_at_k_extended': {},
        'mrr_baseline': 0,
        'mrr_extended': 0,
        'map_baseline': 0,
        'map_extended': 0,
        'individual_results': []
    }

    # read the file contents
    with open(file_path, 'r') as file:
        lines = iter(file.readlines())

    # helper function to skip empty lines and return the next non-empty line
    def next_non_empty_line():
        for line in lines:
            line = line.strip()
            if line:
                return line
        return None

    # parse general information
    data['project'] = int(next_non_empty_line().split()[1][:-1])
    data['total_groundtruth_files'] = int(next_non_empty_line().split()[-1])
    data['total_bugs'] = int(next_non_empty_line().split()[-1])
    data['total_groundtruth_not_found'] = int(next_non_empty_line().split()[-1])
    data['total_bug_reports_no_groundtruth'] = int(next_non_empty_line().split()[-1])
    data['bug_reports_no_groundtruth'] = ast.literal_eval(next_non_empty_line().split(':')[-1][1:])
    data['total_bug_reports_missing_groundtruth'] = int(next_non_empty_line().split()[-1])
    data['bug_reports_missing_groundtruth'] = ast.literal_eval(next_non_empty_line().split(':')[-1][1:])
    data['total_considered_bugs'] = int(next_non_empty_line().split()[-1])

    # collect qe
    data['qe_improved_count'] = int(next_non_empty_line().split()[-1])
    data['qe_identical_count'] = int(next_non_empty_line().split()[-1])
    data['qe_worse_count'] = int(next_non_empty_line().split()[-1])

    # collect hit@k baseline
    next_non_empty_line()
    data['hit_at_k_baseline'] = {
        'hit@1': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
        'hit@5': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
        'hit@10': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
    }

    # collect hit@k extended
    next_non_empty_line()
    data['hit_at_k_extended'] = {
        'hit@1': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
        'hit@5': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
        'hit@10': round(float(next_non_empty_line().split(':')[1].strip().rstrip('%')) / 100, 4),
    }

    # collect mrr
    data['mrr_baseline'] = round(float(next_non_empty_line().split()[-1]), 4)
    data['mrr_extended'] = round(float(next_non_empty_line().split()[-1]), 4)

    # collect map
    data['map_baseline'] = round(float(next_non_empty_line().split()[-1]), 4)
    data['map_extended'] = round(float(next_non_empty_line().split()[-1]), 4)

    # collect individual results
    next_non_empty_line()
    for line in lines:
        line = line.strip()
        if line:
            parts = line.split(',', 2)
            bug_id = int(parts[0].strip())
            bug_type = parts[1].strip().strip("'")
            bug_hits = ast.literal_eval(parts[2])
            data['individual_results'].append((bug_id, bug_type, bug_hits))
    
    
    return data


# loop through all files and store their data
def process_files_in_directory(path, extension):
    all_data = []
    
    for file in os.listdir(path):
        if file.endswith(extension):
            file_path = os.path.join(path, file)
            data = extract_data_from_file(file_path)
            all_data.append(data)
    
    return all_data


def main(evaluation_results_root, organized_data_root):
    
    # get all data
    results_stem = process_files_in_directory(evaluation_results_root, "evaluation_stem.txt")
    results_no_stem = process_files_in_directory(evaluation_results_root, "evaluation_no_stem.txt")
    
    # write all data to files
    write_results_QE(results_stem, organized_data_root, "_stem.txt")
    write_results_QE(results_no_stem, organized_data_root, "_no_stem.txt")
    write_results_hitk(results_stem, organized_data_root, "_stem.txt")
    write_results_hitk(results_no_stem, organized_data_root, "_no_stem.txt")
    write_results_all(results_stem, organized_data_root, "_stem.txt")
    write_results_all(results_no_stem, organized_data_root, "_no_stem.txt")


# Example of how to call the function
if __name__ == "__main__":

    main(evaluation_results_root, organized_data_root)
