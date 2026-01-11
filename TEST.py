import requests
import json
import os
import time

def recuperer_marques_favorites_detaillees():
    url_list = "https://asos2.p.rapidapi.com/products/v2/list"
    
    marques = [
        "Aape By A Bathing Ape",
        "AllSaints",
        "Arket",
        "Paul Smith",
        "PS Paul Smith",
        "Vans"
    ]
    
    headers = {
        "X-RapidAPI-Key": "ad9d8405e4msh50d663f6573d46ep1af517jsn539ffb71fc58",
        "X-RapidAPI-Host": "asos2.p.rapidapi.com"
    }

    toutes_les_pepites = []

    for marque in marques:
        print(f"🔍 Analyse des stocks pour : {marque}...")
        
        querystring = {
            "store": "FR",
            "offset": "0",
            "q": marque,
            "limit": "30",
            "country": "FR",
            "sort": "discount",
            "currency": "EUR",
            "lang": "fr-FR"
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
                        
                        # Extraction des tailles
                        variants = p.get('variants', [])
                        tailles_dispos = [v.get('brandSize', 'N/A') for v in variants if v.get('isInStock')]
                        
                        if not tailles_dispos:
                            tailles_dispos = ["Consulter sur le site"]

                        # Correction Image URL
                        img_url = p.get('imageUrl')
                        if img_url and not img_url.startswith('http'):
                            img_url = "https://" + img_url

                        toutes_les_pepites.append({
                            "id": p.get('id'),
                            "marque": p.get('brandName'),
                            "nom": p.get('name'),
                            "prix_actuel": f"{prix_actuel}€",
                            "prix_base": f"{prix_prev}€",
                            "reduction_valeur": reduction_pct,
                            "reduction_label": f"-{reduction_pct}%",
                            "tailles": tailles_dispos,
                            "image": img_url,
                            "url": f"https://www.asos.com/fr/{p.get('url')}"
                        })
            
            time.sleep(1) # Sécurité pour ne pas être banni de l'API

        except Exception as e:
            print(f"❌ Erreur pour {marque}: {e}")

    # Tri par réduction
    toutes_les_pepites.sort(key=lambda x: x['reduction_valeur'], reverse=True)

    # --- MODIFICATION CRUCIALE POUR GITHUB ACTIONS ---
    # On enregistre dans le dossier courant du projet, pas dans Downloads
    file_name = "tinder_shopping_final.json"
    
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(toutes_les_pepites, f, indent=4, ensure_ascii=False)
            
    print(f"\n🚀 RAPPORT GÉNÉRÉ : {len(toutes_les_pepites)} pépites triées.")
    print(f"📁 Fichier mis à jour : {file_name}")

if __name__ == "__main__":
    recuperer_marques_favorites_detaillees()
