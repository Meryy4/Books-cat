import json
import re
import requests
from pathlib import Path

RAW = Path("data/raw")

def split_into_chapters(text: str) -> list[str]:
    pattern = r"(?im)^CHAPTER\s+[IVXLCDM0-9\.]+"
    raw_chunks = re.split(pattern, text)
    chapters = [chunk.strip() for chunk in raw_chunks if len(chunk.strip()) > 500]
    return chapters

def analyze_chunk(text_chunk: str, model: str = "llama3") -> dict:
    prompt = f"""Évalue l'intensité de ces trois axes de 1 à 10 pour le texte fourni.
    Réponds UNIQUEMENT au format JSON strict avec les clés exactes : "absurde", "peur", "douceur".
    Texte : {text_chunk[:3000]}"""

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        })
        data = response.json()
        
        if "error" in data:
            print(f"\nErreur API Ollama : {data['error']}")
            return {"absurde": 0, "peur": 0, "douceur": 0}
            
        return json.loads(data["response"])
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"\nErreur de décodage JSON : {e}")
        return {"absurde": 0, "peur": 0, "douceur": 0}
    except requests.exceptions.RequestException as e:
        print(f"\nErreur de connexion à Ollama (est-il lancé ?) : {e}")
        return {"absurde": 0, "peur": 0, "douceur": 0}

if __name__ == "__main__":
    alice_path = RAW / "alice_s_adventures_in_wonderland.txt"
    PROCESSED = Path("data/processed")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    
    if alice_path.exists():
        text = alice_path.read_text(encoding="utf-8")
        chapitres = [c for c in split_into_chapters(text) if len(c) > 1000]
        
        livre_data = []
        for i, chap in enumerate(chapitres):
            print(f"Analyse du segment {i+1}/{len(chapitres)}...")
            scores = analyze_chunk(chap)
            livre_data.append({"segment": i+1, "scores": scores})
            
        output_file = PROCESSED / "alice_analysis.json"
        output_file.write_text(json.dumps(livre_data, indent=2), encoding="utf-8")
        print(f"Analyse terminée. Données sauvegardées dans {output_file}")