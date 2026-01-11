import requests
import json
import os
import time

def recuperer_marques_favorites_detaillees():
    url_list = "https://asos2.p.rapidapi.com/products/v2/list"
    file_name = "tinder_shopping_final.json"
    
    marques = [
        "Aape By A Bathing Ape", "AllSaints", "Arket", 
        "Paul Smith", "PS Paul Smith", "Vans"
    ]
    
    headers = {
        "X-RapidAPI-Key": "ad9d8405e4msh50d663f6573d46ep1af517jsn539ffb71fc58",
        "X-RapidAPI-Host": "asos2.p.rapidapi.com"
    }

    nouvelles_pepites = []

    # --- 1. COLLECTE DES NOUVELLES PÉPITES ---
    for marque in marques:
        print(f"🔍 Scan quotidien : {marque}...")
        querystring = {
            "store": "FR", "offset": "0", "q": marque,
            "limit": "40", "country": "FR", "sort": "discount",
            "currency": "EUR", "lang": "fr-FR"
        }

        try:
            response = requests.get(url_list, headers=headers, params=querystring)
            data = response.json()
            products = data.get('products', [])
            
            for p in products:
                brand_name = p.get('brandName', '').lower()
                if marque.lower() in brand_name:
                    prix_actuel = p.get('price', {}).get('current', {}).get('value')
                    prix_prev = p.get('price', {}).get('previous', {}).get('value')
                    
                    if prix_prev and prix_prev > prix_actuel:
                        reduction_pct = round(((prix_prev - prix_actuel) / prix_prev) * 100)
                        
                        # Extraction des tailles dispos
                        variants = p.get('variants', [])
                        tailles_dispos = [v.get('brandSize', 'N/A') for v in variants if v.get('isInStock')]
                        
                        if not tailles_dispos:
                            tailles_dispos = ["Vérifier sur site"]

                        img_url = p.get('imageUrl')
                        if img_url and not img_url.startswith('http'):
                            img_url = "https://" + img_url

                        nouvelles_pepites.append({
                            "id": str(p.get('id')), # ID en string pour la comparaison
                            "marque": p.get('brandName'),
                            "nom": p.get('name'),
                            "prix_actuel": f"{prix_actuel}€",
                            "prix_base": f"{prix_prev}€",
                            "reduction_valeur": reduction_pct,
                            "reduction_label": f"-{reduction_pct}%",
                            "tailles": tailles_dispos,
                            "image": img_url,
                            "url": f"https://www.asos.com/fr/{p.get('url')}",
                            "date_ajout": time.strftime("%Y-%m-%d")
                        })
            time.sleep(1) # Pause anti-ban

        except Exception as e:
            print(f"❌ Erreur sur {marque}: {e}")

    # --- 2. FUSION AVEC L'ANCIEN CATALOGUE (ANTI-DOUBLONS) ---
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                catalogue_existant = json.load(f)
        except:
            catalogue_existant = []
    else:
        catalogue_existant = []

    # On utilise un dictionnaire (clé = ID) pour fusionner. 
    # Les nouvelles pépites écrasent les anciennes si l'ID est identique (mise à jour prix).
    dict_fusion = {str(item['id']): item for item in catalogue_existant}
    for n in nouvelles_pepites:
        dict_fusion[str(n['id'])] = n

    # --- 3. TRI ET NETTOYAGE ---
    # On transforme le dico en liste
    liste_finale = list(dict_fusion.values())
    
    # On trie par le plus gros pourcentage de réduction
    liste_finale.sort(key=lambda x: x['reduction_valeur'], reverse=True)

    # On ne garde que les 150 meilleures pépites pour garantir la performance
    liste_finale = liste_finale[:150]

    # --- 4. SAUVEGARDE ---
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(liste_finale, f, indent=4, ensure_ascii=False)
            
    print(f"\n✨ BASE DE DONNÉES MISE À JOUR")
    print(f"📈 Total dans le catalogue : {len(liste_finale)} pépites (après fusion).")

if __name__ == "__main__":
    recuperer_marques_favorites_detaillees()
