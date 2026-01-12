"""
数据处理保存模块
Knowledge Graph Data Saving Module
"""

import csv
import uuid
import json
import os
from typing import List, Dict, Any

class KGSaver:
    def __init__(self, output_dir: str, project_name: str = "飞行器气动设计"):
        self.output_dir = output_dir
        self.project_name = project_name
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Define path for the triplets CSV file
        self.triplet_csv_file = os.path.join(self.output_dir, "triplets.csv")

    def load_triplets_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Load triplets from a JSON file.
        
        Args:
            json_file_path: Path to the JSON file containing triplets
            
        Returns:
            List of triplet dictionaries
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                triplets = json.load(f)
            print(f"[KGSaver] Loaded {len(triplets)} triplets from '{json_file_path}'")
            return triplets
        except FileNotFoundError:
            print(f"[KGSaver] Error: JSON file not found: {json_file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"[KGSaver] Error decoding JSON: {e}")
            return []
        except Exception as e:
            print(f"[KGSaver] Error loading JSON: {e}")
            return []
    
    def save_triplets(self, raw_triplets: List[Dict[str, Any]] = None, json_file_path: str = None):
        """
        Processes raw triplets from LLM, adds unique IDs,
        maps fields to the required CSV format,
        and saves them to CSV.
        
        Can either accept triplets directly or load them from a JSON file.
        
        Args:
            raw_triplets: Optional list of triplet dictionaries
            json_file_path: Optional path to JSON file containing triplets
            
        raw_triplets format (Expected from LLM based on Prompt):
        [
            {
                "subject": "Wing",
                "subject_type": "Component",
                "relation_type": "is a part of",
                "object": "Aircraft",
                "object_type": "Vehicle",
                "evidence": "The wing is a key component of the aircraft."
            },
            ...
        ]
        """
        # If json_file_path is provided, load triplets from it
        if json_file_path:
            raw_triplets = self.load_triplets_from_json(json_file_path)
        
        # If still no triplets, return
        if not raw_triplets:
            print(f"[KGSaver] No triplets to process.")
            return
        
        processed_triplets = []

        for item in raw_triplets:
            # 1. Generate a unique ID
            unique_id = str(uuid.uuid4())[:8]
            
            # 2. Map LLM fields to CSV fields
            # Extract types with defaults to empty strings if missing
            subject_type = item.get("subject_type", "").strip()
            relation_type = item.get("relation_type", "").strip() # Note: Prompt uses "relation_type"
            object_type = item.get("object_type", "").strip()
            
            # Construct a structured triplet
            processed_triplets.append({
                "id": unique_id,
                "head": item.get("subject", "").strip(),  # Subject -> head
                "head_type": subject_type,         # Subject Type -> head_type
                "relation": relation_type,            # Relation Type -> relation
                "tail": item.get("object", "").strip(),   # Object -> tail
                "tail_type": object_type,           # Object Type -> tail_type
                "evidence": item.get("evidence", "").strip()
            })

        # 3. Save to CSV
        if processed_triplets:
            fieldnames = ['id', 'head', 'head_type', 'relation', 'tail', 'tail_type', 'evidence']
            try:
                with open(self.triplet_csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(processed_triplets)
                print(f"[KGSaver] Saved {len(processed_triplets)} triplets to '{self.triplet_csv_file}'")
            except Exception as e:
                print(f"[KGSaver] Error writing CSV: {e}")
                return
        else:
            print(f"[KGSaver] No triplets to save.")
