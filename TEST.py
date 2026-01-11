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

    print(f"🚀 DÉMARRAGE DU SCAN : {time.strftime('%H:%M:%S')}")

    # --- 1. COLLECTE ---
    for marque in marques:
        print(f"🔍 Analyse en cours : {marque}...")
        querystring = {
            "store": "FR", "offset": "0", "q": marque,
            "limit": "40", "country": "FR", "sort": "discount",
            "currency": "EUR", "lang": "fr-FR"
        }

        try:
            response = requests.get(url_list, headers=headers, params=querystring)
            # Vérification du statut de l'API
            if response.status_code != 200:
                print(f"⚠️ Erreur API ({response.status_code}) pour {marque}")
                continue

            data = response.json()
            products = data.get('products', [])
            trouves_pour_cette_marque = 0
            
            for p in products:
                brand_name = p.get('brandName', '').lower()
                if marque.lower() in brand_name:
                    prix_actuel = p.get('price', {}).get('current', {}).get('value')
                    prix_prev = p.get('price', {}).get('previous', {}).get('value')
                    
                    if prix_prev and prix_prev > prix_actuel:
                        reduction_pct = round(((prix_prev - prix_actuel) / prix_prev) * 100)
                        
                        variants = p.get('variants', [])
                        tailles_dispos = [v.get('brandSize', 'N/A') for v in variants if v.get('isInStock')]
                        
                        img_url = p.get('imageUrl')
                        if img_url and not img_url.startswith('http'):
                            img_url = "https://" + img_url

                        nouvelles_pepites.append({
                            "id": str(p.get('id')),
                            "marque": p.get('brandName'),
                            "nom": p.get('name'),
                            "prix_actuel": f"{prix_actuel}€",
                            "prix_base": f"{prix_prev}€",
                            "reduction_valeur": reduction_pct,
                            "reduction_label": f"-{reduction_pct}%",
                            "tailles": tailles_dispos or ["Vérifier sur site"],
                            "image": img_url,
                            "url": f"https://www.asos.com/fr/{p.get('url')}",
                            "date_ajout": time.strftime("%Y-%m-%d")
                        })
                        trouves_pour_cette_marque += 1
            
            print(f"✅ {marque} : {trouves_pour_cette_marque} pépites ajoutées.")
            time.sleep(1) 

        except Exception as e:
            print(f"❌ Erreur critique sur {marque}: {e}")

    print(f"\n📊 FIN DU SCAN. Total récolté : {len(nouvelles_pepites)} articles.")

    # --- 2. FUSION ET SAUVEGARDE ---
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                catalogue_existant = json.load(f)
            print(f"📂 Catalogue existant chargé ({len(catalogue_existant)} articles).")
        except:
            print("⚠️ Impossible de lire l'ancien fichier, on repart à zéro.")
            catalogue_existant = []
    else:
        print("ℹ️ Aucun fichier existant trouvé. Création d'un nouveau.")
        catalogue_existant = []

    # Fusion anti-doublons
    dict_fusion = {str(item['id']): item for item in catalogue_existant}
    for n in nouvelles_pepites:
        dict_fusion[str(n['id'])] = n

    liste_finale = list(dict_fusion.values())
    liste_finale.sort(key=lambda x: x['reduction_valeur'], reverse=True)
    liste_finale = liste_finale[:150] # Limite

    # --- 3. ÉCRITURE ET DEBUG ---
    print(f"💾 Tentative d'écriture dans {file_name}...")
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(liste_finale, f, indent=4, ensure_ascii=False)
        
        if os.path.exists(file_name):
            taille = os.path.getsize(file_name)
            print(f"✅ SUCCÈS : Fichier créé avec succès ({taille} octets).")
        else:
            print("❌ ERREUR : Le fichier n'apparaît pas sur le disque après l'écriture.")
    except Exception as e:
        print(f"❌ ERREUR d'écriture : {e}")

if __name__ == "__main__":
    recuperer_marques_favorites_detaillees()
