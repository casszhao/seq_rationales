
import argparse
import csv
import json
import logging
import os

import torch

#from transformers import AutoTokenizer
from natsort import natsorted


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", 
                        type=str,
                        default="data/analogies",
                        help="") # TODO
    parser.add_argument("--target_dir", 
                        type=str,
                        default="rationalization_results/analogies/test",
                        help="") # TODO
    parser.add_argument("--baseline_dir", 
                        type=str,
                        default="rationalization_results/analogies/gpt2_exhaustive",
                        help="") # TODO
    parser.add_argument("--output-path", 
                        type=str,
                        default="evaluation_results/analogies/test-old.csv",
                        help="") # TODO
    parser.add_argument("--rational_size_file", 
                    type=str,
                    default=None,
                    help="A file that containing a json obj that maps sample-name to rational-size; rationale_size_ratio will be ignored")

    # parser.add_argument("--tokenizer", 
    #                     type=str,
    #                     default="gpt2-medium",
    #                     help="") # TODO
    args = parser.parse_args()

    data_dir = args.data_dir
    target_dir = args.target_dir
    baseline_dir = args.baseline_dir
    output_path = args.output_path
    # tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    if args.rational_size_file != None:
        with open(args.rational_size_file) as f:
            rational_size_dict = json.load(f)

    rational_sizes = []
    no_distractors = []
    contain_relatives = []
    baseline_approximation_ratios = []

    dirpath, dirnames, filenames = next(os.walk(target_dir))
    # filenames.sort()
    filenames = natsorted(filenames)

    for filename in filenames:
        path_target = os.path.join(dirpath, filename)
        with open(path_target) as f:
            result_target = json.load(f)

        path_data = os.path.join(data_dir, filename)
        if not os.path.exists(path_data):
            logging.warning(f"[Warning] {path_data} not found. Skipping ground truth.")
        else:
            with open(path_data) as f:
                data = json.load(f)

            if args.rational_size_file != None:
                rational_size_override = rational_size_dict[filename]
                rational_size_target = rational_size_override
                importance_scores = torch.tensor(result_target["importance-scores"])
                pos_sorted = torch.argsort(importance_scores, descending=True)
                pos_rational = pos_sorted[:rational_size_target]
            else:
                rational_size_target = result_target["rational-size"]
                pos_rational = torch.tensor(result_target["rational-positions"])

            
            # rational_sizes
            rational_sizes.append(rational_size_target)

            # no_distractors
            non_distractor_rational = (pos_rational < data["distractor"]["start"]) + (pos_rational > data["distractor"]["end"])
            no_distractor = torch.sum(non_distractor_rational) == rational_size_target
            no_distractors.append(no_distractor)

            # contain_relatives
            relative_hits = pos_rational == data["relative"]
            contain_relative = torch.sum(relative_hits) > 0
            contain_relatives.append(contain_relative)

        path_baseline = os.path.join(baseline_dir, filename)
        if not os.path.exists(path_baseline):
            logging.warning(f"[Warning] {path_baseline} not found. Skipping baseline.")
        else:
            with open(path_baseline) as f:
                result_baseline = json.load(f)
            
            if args.rational_size_file != None:
                rational_size_override = rational_size_dict[filename]
                rational_size_baseline = rational_size_override
            else:
                rational_size_baseline = result_baseline["rational-size"]

            # baseline_approximation_ratios
            baseline_approximation_ratio = rational_size_target / rational_size_baseline
            baseline_approximation_ratios.append(baseline_approximation_ratio)
    
    mean_rational_size = torch.mean(torch.tensor(rational_sizes, dtype=torch.float))
    ratio_no_distractor = torch.mean(torch.tensor(no_distractors, dtype=torch.float))
    ratio_contain_relative = torch.mean(torch.tensor(contain_relatives, dtype=torch.float))
    mean_baseline_approximation_ratio = torch.mean(torch.tensor(baseline_approximation_ratios, dtype=torch.float))

    logging.info(f"Mean rational size: {mean_rational_size}")
    logging.info(f"Ratio no distractor: {ratio_no_distractor}")
    logging.info(f"Ratio contain relative: {ratio_contain_relative}")
    logging.info(f"Mean baseline approximation ratio: {mean_baseline_approximation_ratio}")

    with open(output_path, "w", newline="") as csv_f:
        writer = csv.writer(csv_f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([ "Mean rational size", "Ratio no distractor", "Ratio contain relative", "Mean baseline approximation ratio" ])
        writer.writerow([ mean_rational_size.item(), ratio_no_distractor.item(), ratio_contain_relative.item(), mean_baseline_approximation_ratio.item() ])
