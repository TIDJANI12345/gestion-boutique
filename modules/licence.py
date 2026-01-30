import os
import json
import hashlib
import platform
import requests
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from tkinter import messagebox
from config import DATA_DIR  # ✅ IMPORTER CONFIG

# --- CONFIGURATION ---
URL_SERVEUR = "https://gbserver.pythonanywhere.com"

# ✅ UTILISER DATA_DIR depuis config.py
FICHIER_LICENCE = os.path.join(DATA_DIR, "licence.key")

# Clé de cryptage locale
CLE_CRYPTAGE = b'gAAAAABk_super_secret_key_change_me_later_==' 

class GestionLicence:
    def __init__(self):
        key_fixe = b'Op-Mh72sA8X9F2d5J8q4z7X9v6A3d2G5h8J9k1L2m3n=' 
        self.cipher = Fernet(key_fixe)
        
        # ✅ S'assurer que DATA_DIR existe
        os.makedirs(DATA_DIR, exist_ok=True)

    def get_machine_id(self):
        """Génère un identifiant unique pour cet ordinateur"""
        info = f"{platform.node()}-{platform.system()}-{platform.machine()}-{uuid.getnode()}"
        return hashlib.sha256(info.encode()).hexdigest()

    def verifier_locale(self):
        """Vérifie si une licence valide est stockée localement"""
        if not os.path.exists(FICHIER_LICENCE):
            return False, "Aucune licence trouvée"

        try:
            with open(FICHIER_LICENCE, 'rb') as f:
                data_crypt = f.read()
            
            data_json = self.cipher.decrypt(data_crypt).decode()
            data = json.loads(data_json)
            
            # Vérification machine (Anti-copie)
            if data['machine_id'] != self.get_machine_id():
                return False, "Cette licence est liée à un autre ordinateur"
            
            # Vérification expiration
            date_exp = datetime.strptime(data['expiration'], "%Y-%m-%d")
            if datetime.now() > date_exp:
                return False, f"Licence expirée le {data['expiration']}"
                
            return True, f"Licence valide jusqu'au {data['expiration']}"

        except Exception as e:
            return False, f"Fichier de licence corrompu: {str(e)}"

    def activer_en_ligne(self, cle):
        """Contacte le serveur pour activer la clé"""
        machine_id = self.get_machine_id()
        
        try:
            payload = {
                'cle': cle.strip(),
                'machine_id': machine_id
            }
            
            print(f"📡 Connexion à {URL_SERVEUR}...")
            response = requests.post(f"{URL_SERVEUR}/api/activer", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('succes'):
                    # Sauvegarde locale cryptée
                    donnees_locales = {
                        'cle': cle,
                        'machine_id': machine_id,
                        'expiration': data['expiration'][:10],
                        'type': data['type'],
                        'derniere_verif': datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    json_str = json.dumps(donnees_locales)
                    encrypted_data = self.cipher.encrypt(json_str.encode())
                    
                    with open(FICHIER_LICENCE, 'wb') as f:
                        f.write(encrypted_data)
                        
                    return True, "Activation réussie !"
                else:
                    return False, data.get('message', 'Erreur inconnue')
            else:
                try:
                    err = response.json().get('message')
                except:
                    err = f"Erreur serveur {response.status_code}"
                return False, err
                
        except requests.exceptions.ConnectionError:
            return False, "Impossible de contacter le serveur (Vérifiez internet)"
        except Exception as e:
            return False, f"Erreur technique : {str(e)}"