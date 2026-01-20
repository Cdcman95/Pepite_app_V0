import requests
import json
import os
import time
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AsosScanner:
    def __init__(self):
        self.url_list = "https://asos2.p.rapidapi.com/products/v2/list"
        self.file_name = "tinder_shopping_final.json"
        self.api_key = os.getenv("RAPIDAPI_KEY", "ad9d8405e4msh50d663f6573d46ep1af517jsn539ffb71fc58")
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "asos2.p.rapidapi.com"
        }
        self.request_count = 0
        self.max_requests = 500
        self.marques = [
            "Aape By A Bathing Ape", "AllSaints", "Arket", 
            "Paul Smith", "PS Paul Smith", "Vans", 
            "Farah", "Rains", "Lacoste", "Carhartt WIP", 
            "Fred Perry", "The North Face", "Adidas Originals",
            "Nike", "New Balance", "Dickies"
        ]
    
    def est_article_homme(self, product):
        """Vérifie si l'article est pour homme"""
        gender = product.get('gender', '').lower()
        return 'men' in gender or 'homme' in gender
    
    def extraire_image_valide(self, product):
        """Extrait une URL d'image valide"""
        img_url = product.get('imageUrl', '')
        if not img_url:
            return None
        
        if not img_url.startswith('http'):
            img_url = "https://" + img_url
        
        # Vérifier que ce n'est pas un placeholder
        if 'placeholder' in img_url.lower() or 'default' in img_url.lower():
            return None
        
        return img_url
    
    def calculer_reduction(self, prix_actuel, prix_prev):
        """Calcule le pourcentage de réduction"""
        if not prix_prev or not prix_actuel or prix_prev <= prix_actuel:
            return 0
        return round(((prix_prev - prix_actuel) / prix_prev) * 100)
    
    def scanner_marque(self, marque, nb_pages=3):
        """Scanne une marque sur plusieurs pages"""
        pepites = []
        
        for page in range(nb_pages):
            if self.request_count >= self.max_requests:
                logger.warning(f"⚠️ Limite API atteinte ({self.max_requests} requêtes)")
                return pepites
            
            offset = page * 48
            querystring = {
                "store": "FR",
                "offset": str(offset),
                "q": marque,
                "limit": "48",
                "country": "FR",
                "sort": "pricedesc",  # Essayer aussi "freshness" pour nouveautés
                "currency": "EUR",
                "lang": "fr-FR",
                "gender": "men"  # Forcer le filtre homme
            }
            
            try:
                response = requests.get(
                    self.url_list, 
                    headers=self.headers, 
                    params=querystring,
                    timeout=10
                )
                self.request_count += 1
                
                if response.status_code == 429:
                    logger.warning("⏳ Rate limit atteint, pause de 5s...")
                    time.sleep(5)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"❌ Erreur {response.status_code} pour {marque}")
                    break
                
                data = response.json()
                products = data.get('products', [])
                
                if not products:
                    break
                
                for p in products:
                    # Filtres de qualité
                    if not self.est_article_homme(p):
                        continue
                    
                    prix_actuel = p.get('price', {}).get('current', {}).get('value')
                    prix_prev = p.get('price', {}).get('previous', {}).get('value')
                    
                    reduction_pct = self.calculer_reduction(prix_actuel, prix_prev)
                    
                    # Filtre : minimum 30% de réduction
                    if reduction_pct < 30:
                        continue
                    
                    img_url = self.extraire_image_valide(p)
                    if not img_url:
                        continue
                    
                    # Extraction des tailles disponibles
                    tailles = [
                        v.get('brandSize', 'N/A') 
                        for v in p.get('variants', []) 
                        if v.get('isInStock')
                    ]
                    
                    if not tailles:
                        tailles = ["Vérifier sur le site"]
                    
                    pepites.append({
                        "id": str(p.get('id')),
                        "marque": p.get('brandName', marque),
                        "nom": p.get('name', 'Article sans nom'),
                        "prix_actuel": f"{prix_actuel}€",
                        "prix_base": f"{prix_prev}€",
                        "reduction_valeur": reduction_pct,
                        "reduction_label": f"-{reduction_pct}%",
                        "tailles": tailles,
                        "image": img_url,
                        "url": f"https://www.asos.com/fr/{p.get('url', '')}",
                        "date_ajout": datetime.now().strftime("%Y-%m-%d"),
                        "categorie": p.get('productType', 'Vêtement')
                    })
                
                # Délai entre requêtes
                time.sleep(0.8)
                
            except requests.exceptions.Timeout:
                logger.error(f"⏱️ Timeout pour {marque} page {page}")
                break
            except Exception as e:
                logger.error(f"⚠️ Erreur sur {marque} page {page}: {e}")
                break
        
        return pepites
    
    def fusionner_catalogues(self, nouvelles_pepites):
        """Fusionne avec l'ancien catalogue sans doublons"""
        ancien_catalogue = []
        
        if os.path.exists(self.file_name):
            try:
                with open(self.file_name, "r", encoding="utf-8") as f:
                    ancien_catalogue = json.load(f)
                logger.info(f"📂 Ancien catalogue chargé : {len(ancien_catalogue)} articles")
            except json.JSONDecodeError:
                logger.warning("⚠️ Fichier JSON corrompu, création d'un nouveau")
        
        # Fusion par ID
        dict_final = {str(item['id']): item for item in ancien_catalogue}
        for item in nouvelles_pepites:
            dict_final[str(item['id'])] = item
        
        # Tri par réduction décroissante
        liste_triee = sorted(
            dict_final.values(), 
            key=lambda x: x['reduction_valeur'], 
            reverse=True
        )
        
        # Limite à 400 pour optimiser les perfs mobile
        return liste_triee[:400]
    
    def sauvegarder_catalogue(self, catalogue):
        """Sauvegarde le catalogue en JSON"""
        try:
            with open(self.file_name, "w", encoding="utf-8") as f:
                json.dump(catalogue, f, indent=4, ensure_ascii=False)
            logger.info(f"💾 Catalogue sauvegardé : {len(catalogue)} pépites")
            
            # Stats
            total_economies = sum(
                float(p['prix_base'].replace('€', '')) - float(p['prix_actuel'].replace('€', ''))
                for p in catalogue
            )
            logger.info(f"💰 Économies potentielles totales : {total_economies:.2f}€")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde : {e}")
    
    def executer_scan_complet(self):
        """Lance le scan complet de toutes les marques"""
        logger.info(f"🚀 DÉMARRAGE DU SCAN - {datetime.now().strftime('%H:%M:%S')}")
        
        toutes_les_pepites = []
        
        for i, marque in enumerate(self.marques, 1):
            logger.info(f"🔍 [{i}/{len(self.marques)}] Scan : {marque}")
            pepites = self.scanner_marque(marque, nb_pages=3)
            toutes_les_pepites.extend(pepites)
            logger.info(f"   ✅ {len(pepites)} pépites trouvées")
        
        logger.info(f"\n📊 SCAN TERMINÉ : {len(toutes_les_pepites)} nouveaux articles")
        
        # Fusion et sauvegarde
        catalogue_final = self.fusionner_catalogues(toutes_les_pepites)
        self.sauvegarder_catalogue(catalogue_final)
        
        logger.info(f"✨ Requêtes API utilisées : {self.request_count}/{self.max_requests}")

def main():
    scanner = AsosScanner()
    scanner.executer_scan_complet()

if __name__ == "__main__":
    main()
