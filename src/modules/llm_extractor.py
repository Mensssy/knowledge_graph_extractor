"""
LLM提取三元组模块
LLM Extraction Module for Triplets
"""

import json
import openai
import os
from typing import List, Dict, Any

class LLMExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prompt_template = config['llm']['prompt_template']
        self.model = config['llm']['model']
        self.provider = config['llm'].get('provider', 'openai')

        # Initialize Client
        if self.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY') or config['llm'].get('api_key')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment or config.")
            
            # Check if custom base_url is provided (for DashScope or other compatible APIs)
            base_url = config['llm'].get('base_url')
            if base_url:
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = openai.OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def extract_triplets(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts knowledge triplets (Subject, Predicate, Object, Evidence)
        from the provided text using the configured LLM and Prompt.
        """
        prompt = self.prompt_template.format(text=text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful JSON data generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            try:
                data = json.loads(content)
                # Expecting format: { "triplets": [...] }
                if isinstance(data, dict) and 'triplets' in data:
                    return data['triplets']
                elif isinstance(data, list):
                    # Fallback if LLM returns just a list directly
                    return data
                else:
                    print(f"Warning: Unexpected JSON structure. Keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
                    return []
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse JSON. Response: {content[:200]}...")
                return []

        except openai.APIError as e:
            print(f"LLM API Error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during extraction: {e}")
            return []
