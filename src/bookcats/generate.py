import json
from pathlib import Path

def generate_cat_svg(scores_data: list, output_path: Path):
    chapitres = len(scores_data)
    if chapitres == 0: return
        
    avg_peur = sum(c["scores"].get("peur", 0) for c in scores_data) / chapitres
    avg_douceur = sum(c["scores"].get("douceur", 0) for c in scores_data) / chapitres
    avg_absurde = sum(c["scores"].get("absurde", 0) for c in scores_data) / chapitres
    
    emotions = {"peur": avg_peur, "douceur": avg_douceur, "absurde": avg_absurde}
    dominant = max(emotions, key=emotions.get)
    
    titre_roman = output_path.stem.replace('_', ' ').upper()
    if "ALICE" in titre_roman: titre_roman = "ALICE IN WONDERLAND"
    
    # 1. MOTEUR CHROMATIQUE ET LUMINEUX
    if dominant == "peur":
        bg_grad = '<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#050000"/><stop offset="100%" stop-color="#330000"/></linearGradient>'
        cat_color = "url(#catGradFear)"
        aura_color = "#ff1a1a"
        eye_color = "#ff1a1a"
        smile = ""
        tail_style = 'opacity="0.9"'
    elif dominant == "douceur":
        bg_grad = '<radialGradient id="bg" cx="50%" cy="50%" r="75%"><stop offset="0%" stop-color="#1b2735"/><stop offset="100%" stop-color="#090a0f"/></radialGradient>'
        cat_color = "url(#catGradSweet)"
        aura_color = "#d4af37"
        eye_color = "#d4af37"
        smile = ""
        tail_style = 'opacity="0.9"'
    else: # ARCHÉTYPE CHESHIRE (Absurde)
        bg_grad = '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#1a0033"/><stop offset="100%" stop-color="#000000"/></linearGradient>'
        cat_color = "url(#catGradAbsurd)"
        aura_color = "#ff00ff" # Magenta/Pink accents
        eye_color = "#00ffcc"  # Cyan eyes for surreal contrast
        # The wide, knowing grin
        smile = f'<path d="M 180 175 Q 250 {185 + avg_absurde*4} 320 175 Q 250 215 180 175 Z" fill="#ffffff" filter="url(#glow)" opacity="0.8"/>'
        tail_style = 'opacity="0.7" stroke-dasharray="10 15"' # Vanishing smoke tail

    # 2. DÉCORS
    bg_elements = ""
    if dominant == "peur":
        for i in range(15): bg_elements += f'<path d="M 0 {700-i*40} Q {250+(i%2)*100} {650-i*60} 500 {700-i*30}" stroke="{aura_color}" stroke-width="1" fill="none" opacity="0.1" filter="url(#glow)"/>'
    elif dominant == "douceur":
        for i in range(60):
            x, y, r = (i*47)%500, (i*83)%800, 1 + (i%3)*1.5
            bg_elements += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" opacity="{0.1 + (i%5)*0.15}" filter="url(#glow)"/>'
    else:
        for i in range(12):
            x, y, r = (i*81)%500, (i*113)%800, 10 + (i%5)*20
            bg_elements += f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{aura_color}" stroke-width="2" opacity="0.3" filter="url(#glow)" stroke-dasharray="5 10"/>'

    # 3. ANATOMIE COMPLÈTE
    if dominant == "peur":
        head = 'M 250 240 C 170 240, 180 170, 190 130 L 160 60 L 210 110 Q 250 125, 290 110 L 340 60 L 310 130 C 320 170, 330 240, 250 240 Z'
        body = 'M 210 230 Q 120 350, 140 550 L 120 570 L 380 570 L 360 550 Q 380 350, 290 230 Z'
        l_eye = f'<polygon points="190,160 220,150 205,165" fill="{eye_color}" filter="url(#glow)"/>'
        r_eye = f'<polygon points="310,160 280,150 295,165" fill="{eye_color}" filter="url(#glow)"/>'
    elif dominant == "douceur":
        head = 'M 250 240 C 160 240, 160 140, 185 120 Q 170 80, 205 95 Q 250 110, 295 95 Q 330 80, 315 120 C 340 140, 340 240, 250 240 Z'
        body = 'M 200 230 C 140 300, 160 480, 130 570 L 370 570 C 340 480, 360 300, 300 230 Z'
        l_eye = f'<path d="M 190 155 Q 210 165 230 155" fill="none" stroke="{eye_color}" stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>'
        r_eye = f'<path d="M 270 155 Q 290 165 310 155" fill="none" stroke="{eye_color}" stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>'
    else:
        # Floating, vanishing posture for Absurd
        asym = avg_absurde * 6
        head = f'M 250 240 C 160 250, 170 150, 180 130 Q 140 {80-asym}, 200 110 Q 250 130, 300 110 Q {360+asym} 70, 320 140 C 330 160, 330 230, 250 240 Z'
        # Body tapers off and vanishes instead of hitting the floor
        body = f'M 210 230 Q {120-asym} 350, 200 500 Q 250 550, 300 500 Q {380+asym} 350, 290 230 Z'
        # Oversized, asymmetrical eyes
        l_eye = f'<circle cx="195" cy="140" r="16" fill="{eye_color}" filter="url(#glow)"/><circle cx="195" cy="140" r="6" fill="#000"/>'
        r_eye = f'<circle cx="305" cy="130" r="9" fill="{eye_color}" filter="url(#glow)"/><polygon points="300,125 310,135 300,135" fill="#000"/>'

    # 4. LA QUEUE NARRATIVE
    tail = "M 250 500 " if dominant == "absurde" else "M 250 560 "
    curr_y = 500 if dominant == "absurde" else 560
    for i, chap in enumerate(scores_data):
        p, d, a = chap["scores"].get("peur", 0), chap["scores"].get("douceur", 0), chap["scores"].get("absurde", 0)
        curr_y += 15 + (d * 1.5)
        offset = (p * 12) * (-1 if i % 2 == 0 else 1)
        if dominant == "peur":
            tail += f"L {250 + offset} {curr_y} " 
        elif dominant == "absurde":
            tail += f"Q {250 + offset + (a*8)} {curr_y - 20}, {250 + offset} {curr_y} "
        else:
            tail += f"S {250 + offset/2} {curr_y - 10}, {250 + offset} {curr_y} "

    # 5. ASSEMBLAGE SVG
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 950" width="100%" height="100%">
    <defs>
        {bg_grad}
        <radialGradient id="catGradFear" cx="50%" cy="30%" r="70%"><stop offset="0%" stop-color="#2a0000"/><stop offset="100%" stop-color="#000000"/></radialGradient>
        <radialGradient id="catGradSweet" cx="50%" cy="30%" r="70%"><stop offset="0%" stop-color="#2c3e50"/><stop offset="100%" stop-color="#0f172a"/></radialGradient>
        <!-- Cheshire Fade: Magenta fades entirely into transparency at the edges/bottom -->
        <radialGradient id="catGradAbsurd" cx="50%" cy="30%" r="70%"><stop offset="0%" stop-color="#cc00ff" stop-opacity="0.8"/><stop offset="100%" stop-color="#4a0080" stop-opacity="0.0"/></radialGradient>
        
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur2" />
            <feMerge><feMergeNode in="blur2" /><feMergeNode in="blur1" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="15" stdDeviation="10" flood-color="#000000" flood-opacity="0.9"/>
        </filter>
    </defs>
    
    <rect width="100%" height="100%" fill="url(#bg)"/>
    {bg_elements}
    
    <circle cx="250" cy="300" r="180" fill="{aura_color}" opacity="0.04" filter="url(#glow)"/>
    
    <!-- Queue -->
    <path d="{tail}" fill="none" stroke="{aura_color}" stroke-width="5" stroke-linejoin="round" filter="url(#glow)" {tail_style}/>
    <path d="{tail}" fill="none" stroke="#ffffff" stroke-width="2" stroke-linejoin="round" {tail_style}/>
    
    <!-- Corps & Tête -->
    <path d="{body}" fill="{cat_color}" filter="url(#shadow)"/>
    <path d="{head}" fill="{cat_color}" filter="url(#shadow)"/>
    
    <!-- Visage -->
    {l_eye}
    {r_eye}
    {smile}
    
    <text x="250" y="900" font-family="Georgia, serif" font-size="28" fill="#ffffff" text-anchor="middle" letter-spacing="6" opacity="0.9" filter="url(#shadow)">{titre_roman}</text>
    <text x="250" y="925" font-family="Arial, sans-serif" font-size="10" fill="{aura_color}" text-anchor="middle" letter-spacing="4" opacity="0.6">EMOTIONAL DATA PORTRAIT</text>
    </svg>"""
    output_path.write_text(svg_content, encoding="utf-8")

if __name__ == "__main__":
    PROCESSED = Path("data/processed")
    for json_file in PROCESSED.glob("*.json"):
        svg_file = PROCESSED / f"{json_file.stem}.svg"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        generate_cat_svg(data, svg_file)
        print(f"Affiche générée : {svg_file}")