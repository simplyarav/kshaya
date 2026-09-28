import re
import os

class Classifier:
    # Extremely simplified regex for demonstration
    RULES = {
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "API_KEY": re.compile(r"AKIA[0-9A-Z]{16}")
    }

    @staticmethod
    def scan_file(filepath: str) -> list:
        flags = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024 * 1024) # Scan first 1MB only for safety
                for rule_name, pattern in Classifier.RULES.items():
                    if pattern.search(content):
                        flags.append(rule_name)
        except Exception:
            pass
        return flags
