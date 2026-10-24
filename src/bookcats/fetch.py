import requests, re
from pathlib import Path

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

def slug(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')

def strip_gutenberg(text: str) -> str:
    pattern = r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*(.*?)\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()

def fetch_book(title: str) -> str:
    cache = RAW / f"{slug(title)}.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    
    meta = requests.get("https://gutendex.com/books/", params={"search": title}, timeout=120).json()
    if not meta["results"]:
        raise ValueError(f"Aucun livre trouvé pour : {title}")
        
    book = meta["results"][0]
    
    url = next((link for mime, link in book["formats"].items() if mime.startswith("text/plain")), None)
    if not url:
        raise ValueError(f"Format texte brut introuvable pour : {title}")
        
    text = requests.get(url, timeout=120).text
    text = strip_gutenberg(text)
    
    cache.write_text(text, encoding="utf-8")
    return text

if __name__ == "__main__":
    livres = [
        "Alice's Adventures in Wonderland",
        "Dracula",
        "Frankenstein",
        "The Picture of Dorian Gray",
        "The Metamorphosis",
        "Pride and Prejudice",
        "The Time Machine",
        "A Tale of Two Cities",
        "The War of the Worlds",
        "The Jungle Book"
    ]
    
    for titre in livres:
        print(f"Récupération de '{titre}'...")
        try:
            texte = fetch_book(titre)
            print(f"  -> Succès ({len(texte)} caractères).")
        except Exception as e:
            print(f"  -> Erreur : {e}")