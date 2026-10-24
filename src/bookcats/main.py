import json
from pathlib import Path
from fetch import fetch_book, slug
from analyze import split_into_chapters, analyze_chunk
from generate import generate_cat_svg

def run_pipeline():
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

    PROCESSED = Path("data/processed")
    PROCESSED.mkdir(parents=True, exist_ok=True)

    for titre in livres:
        print(f"\n--- Traitement de : {titre} ---")
        
        # 1. Récupération
        try:
            texte = fetch_book(titre)
        except Exception as e:
            print(f"Erreur de téléchargement : {e}")
            continue
            
        nom_fichier = slug(titre)
        json_path = PROCESSED / f"{nom_fichier}.json"
        svg_path = PROCESSED / f"{nom_fichier}.svg"
        
        # 2. Analyse via Llama 3 (uniquement si le JSON n'existe pas déjà)
        if not json_path.exists():
            print("Analyse des chapitres avec Llama 3...")
            chapitres = [c for c in split_into_chapters(texte) if len(c) > 1000]
            livre_data = []
            for i, chap in enumerate(chapitres):
                print(f"  Segment {i+1}/{len(chapitres)}")
                scores = analyze_chunk(chap)
                livre_data.append({"segment": i+1, "scores": scores})
            
            json_path.write_text(json.dumps(livre_data, indent=2), encoding="utf-8")
        else:
            print("Analyse JSON déjà existante.")
            
        # 3. Génération SVG
        print("Génération du chat SVG...")
        data = json.loads(json_path.read_text(encoding="utf-8"))
        generate_cat_svg(data, svg_path)
        print(f"Terminé ! -> {svg_path}")

if __name__ == "__main__":
    run_pipeline()