import os
import json
import hashlib
import platform
import requests
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from tkinter import messagebox
from config import DATA_DIR
from modules.logger import get_logger

logger = get_logger('licence')

# --- CONFIGURATION ---
URL_SERVEUR = "https://gbserver.pythonanywhere.com"

FICHIER_LICENCE = os.path.join(DATA_DIR, "licence.key")

# Cle de chiffrement par defaut (fallback si variable d'environnement non definie)
_CLE_DEFAUT = b'Op-Mh72sA8X9F2d5J8q4z7X9v6A3d2G5h8J9k1L2m3n='


class GestionLicence:
    def __init__(self):
        # Charger la cle depuis variable d'environnement ou utiliser le fallback
        cle_env = os.environ.get('GB_LICENCE_KEY')
        if cle_env:
            key = cle_env.encode() if isinstance(cle_env, str) else cle_env
        else:
            key = _CLE_DEFAUT
        self.cipher = Fernet(key)

        os.makedirs(DATA_DIR, exist_ok=True)

    def get_machine_id(self):
        """Genere un identifiant unique pour cet ordinateur"""
        info = f"{platform.node()}-{platform.system()}-{platform.machine()}-{uuid.getnode()}"
        return hashlib.sha256(info.encode()).hexdigest()

    def verifier_locale(self):
        """Verifie si une licence valide est stockee localement"""
        if not os.path.exists(FICHIER_LICENCE):
            return False, "Aucune licence trouvee"

        try:
            with open(FICHIER_LICENCE, 'rb') as f:
                data_crypt = f.read()

            data_json = self.cipher.decrypt(data_crypt).decode()
            data = json.loads(data_json)

            # Verification machine (Anti-copie)
            if data['machine_id'] != self.get_machine_id():
                return False, "Cette licence est liee a un autre ordinateur"

            # Verification expiration
            date_exp = datetime.strptime(data['expiration'], "%Y-%m-%d")
            if datetime.now() > date_exp:
                return False, f"Licence expiree le {data['expiration']}"

            return True, f"Licence valide jusqu'au {data['expiration']}"

        except Exception as e:
            logger.error(f"Erreur verification licence : {e}")
            return False, f"Fichier de licence corrompu: {str(e)}"

    def activer_en_ligne(self, cle):
        """Contacte le serveur pour activer la cle"""
        machine_id = self.get_machine_id()

        try:
            payload = {
                'cle': cle.strip(),
                'machine_id': machine_id
            }

            logger.info(f"Tentative d'activation licence...")
            response = requests.post(f"{URL_SERVEUR}/api/activer", json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('succes'):
                    # Sauvegarde locale cryptee
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

                    logger.info("Activation licence reussie")
                    return True, "Activation reussie !"
                else:
                    msg = data.get('message', 'Erreur inconnue')
                    logger.warning(f"Activation refusee : {msg}")
                    return False, msg
            else:
                try:
                    err = response.json().get('message')
                except Exception:
                    err = f"Erreur serveur {response.status_code}"
                logger.error(f"Erreur activation : {err}")
                return False, err

        except requests.exceptions.ConnectionError:
            logger.error("Serveur licence injoignable")
            return False, "Impossible de contacter le serveur (Verifiez internet)"
        except Exception as e:
            logger.error(f"Erreur technique activation : {e}")
            return False, f"Erreur technique : {str(e)}"
