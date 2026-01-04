import requests, json, time

INVENTORY_URL = "http://inventory:1337/inventory"
TARGETS_FILE = "/etc/prometheus/targets.json"
PORT = 9100

def update_targets():
    try:
        sensors = requests.get(INVENTORY_URL, timeout=5).json()
        targets = [f"{s}:{PORT}" for s in sensors]
        data = [{"targets": targets}]
        with open(TARGETS_FILE, "w") as f:
            json.dump(data, f)
        print(f" Updated {len(targets)} targets: {targets}")
    except Exception as e:
        print(f"Error updating targets: {e}")

if __name__ == "__main__":
    while True:
        update_targets()
        time.sleep(5)
