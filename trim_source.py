import json
import argparse

def main(input_file: str, output_file: str, new_start_time: int) -> None:
    with open(input_file, "r") as f:
        data = json.load(f)
    meta_tags = data["metadata_tags"]
    for track in meta_tags:
        for tag in meta_tags[track]["tags"]:
            tag["start_time"] -= new_start_time
            tag["end_time"] -= new_start_time
    with open(output_file, "w") as f:
        json.dump(data, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim metadata tags in a JSON file.")
    parser.add_argument("--input_file", type=str, help="Input JSON file with metadata tags")
    parser.add_argument("--output_file", type=str, help="Output JSON file with trimmed metadata tags")
    parser.add_argument("--new_start_time", type=int, help="New start time to subtract from all tags")
    args = parser.parse_args()
    main(args.input_file, args.output_file, args.new_start_time)