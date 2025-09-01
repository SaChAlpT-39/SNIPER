import yaml, json
with open('config/api_limits.yml','r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
print(json.dumps(data, indent=2))
