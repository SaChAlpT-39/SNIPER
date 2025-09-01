from modules_utils.config_loader import ConfigLoader

loader = ConfigLoader("config")
print(loader.load_risk())
print(loader.load_system())
api = loader.load_api_limits()
print(loader.summarize_limits(api))
