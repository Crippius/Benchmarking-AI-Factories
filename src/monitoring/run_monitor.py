# monitors/run_monitor.py
import yaml
from services.ollama_monitor import OllamaMonitor
# from services.chroma_monitor import ChromaMonitor
# from services.postgres_monitor import PostgresMonitor

def load_recipe(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_monitor(recipe):
    monitor_type = recipe["type"]
    if monitor_type == "ollama":
        return OllamaMonitor(**recipe)
    # TODO
    # elif monitor_type == "chroma":
    #     return ChromaMonitor(**recipe)
    # elif monitor_type == "postgres":
    #     return PostgresMonitor(**recipe)
    else:
        raise ValueError(f"Unknown monitor type: {monitor_type}")

if __name__ == "__main__":
    recipe = load_recipe("monitor_recipes/ollama_monitor.yaml")
    monitor = get_monitor(recipe)
    monitor.start()
