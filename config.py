import yaml

def load_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)
    
config = load_config()