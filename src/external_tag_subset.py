import json

def trim_tags(input_file: str, output_file: str, end_time: int) -> None:
    with open(input_file, "r") as f:
        data = json.load(f)
    meta_tags = data["metadata_tags"]
    for track in meta_tags:
        meta_tags[track]["tags"] = [tag for tag in meta_tags[track]["tags"] if tag["end_time"] <= end_time]
    with open(output_file, "w") as f:
        json.dump(data, f)