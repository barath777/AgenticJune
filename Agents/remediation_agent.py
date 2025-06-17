from pathlib import Path
import json
import subprocess
import os
import yaml

class RemediationAgent:
    def __init__(self, mapping_file=None):
        # Get the root of the Alert_System project regardless of where this file is run from
        project_root = Path(__file__).resolve().parents[1]  # Adjust if deeper
        #default_mapping_path = project_root / "Mapping" / "mapping.json"
        default_mapping_path = project_root / "Mapping" / "mapping.yml"  # 🔄 Use .yml

        mapping_file = Path(mapping_file) if mapping_file else default_mapping_path

        if not mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found at {mapping_file}")

        with open(mapping_file, 'r') as f:
            #self.action_map = json.load(f)
            self.action_map = yaml.safe_load(f)  # 🔄 Load YAML

    def perform_remediation(self, action_types: list[str]):
        executed = []
        errors = []

        for action in action_types:
            task_name = self.action_map.get(action)
            if task_name:
                try:
                    result = subprocess.run(["schtasks", "/run", "/tn", task_name], check=True, shell=True)
                    print(f"[INFO] Output for '{action}':\n{result.stdout}")
                    executed.append({"action": action, "task": task_name, "status": "success"})
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Script '{task_name}' failed with error:\n{e.stderr}")
                    errors.append({
                        "action": action,
                        "task": task_name,
                        "status": "failed",
                        "error": str(e)
                    })
            else:
                print(f"[WARN] No mapping found for action '{action}'")
                errors.append({
                    "action": action,
                    "status": "not found in mapping"
                })

        return {
            "executed": executed,
            "errors": errors
        }
