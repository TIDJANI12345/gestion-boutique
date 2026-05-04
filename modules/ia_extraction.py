"""
Module d'extraction IA depuis exports WhatsApp
Utilise Google Gemini API
"""
import json
import re
import zipfile
import os
from datetime import datetime
from modules.logger import get_logger
from modules.produits import Produit
import shutil
from pathlib import Path

logger = get_logger('ia_extraction')

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai non installé. pip install google-generativeai")


class IAExtraction:

    @staticmethod
    def configurer_gemini(api_key):
        """Configurer l'API Gemini"""
        if not GEMINI_AVAILABLE:
            return False, "Module google-generativeai non installé"

        try:
            genai.configure(api_key=api_key)
            return True, "API Gemini configurée"
        except Exception as e:
            logger.error(f"Erreur config Gemini: {e}")
            return False, str(e)

    @staticmethod
    def extraire_zip_whatsapp(zip_path, temp_dir):
        """Extraire le contenu du ZIP WhatsApp"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Trouver le fichier .txt de messages
            txt_files = list(Path(temp_dir).glob("*.txt"))
            if not txt_files:
                return None, [], "Aucun fichier .txt trouvé"

            messages_file = txt_files[0]

            # Lister les images
            images = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                images.extend(Path(temp_dir).glob(ext))

            return messages_file, images, "OK"

        except Exception as e:
            logger.error(f"Erreur extraction ZIP: {e}")
            return None, [], str(e)

    @staticmethod
    def parser_messages_whatsapp(txt_path):
        """Parser le fichier texte WhatsApp (multi-format)"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            parsed = []

            # Format 1: [DD/MM/YYYY, HH:MM:SS] Nom: Message
            pattern1 = r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+?):\s*(.+?)(?=\[\d{1,2}/\d{1,2}/\d{2,4}|$)'
            matches1 = re.findall(pattern1, content, re.DOTALL)

            # Format 2: DD/MM/YYYY, HH:MM:SS - Nom: Message (sans crochets)
            pattern2 = r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([^:]+?):\s*(.+?)(?=\d{1,2}/\d{1,2}/\d{2,4}|$)'
            matches2 = re.findall(pattern2, content, re.DOTALL)

            # Format 3: DD.MM.YY, HH:MM - Nom: Message (points)
            pattern3 = r'(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*-?\s*([^:]+?):\s*(.+?)(?=\d{1,2}\.\d{1,2}\.\d{2,4}|$)'
            matches3 = re.findall(pattern3, content, re.DOTALL)

            # Combiner tous les matches
            all_matches = matches1 + matches2 + matches3

            logger.info(f"Formats détectés - Format1: {len(matches1)}, Format2: {len(matches2)}, Format3: {len(matches3)}")

            if not all_matches:
                # Fallback: parser ligne par ligne simple
                logger.warning("Aucun format standard détecté, tentative parsing simple")
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if len(line) > 10 and ':' in line:
                        # Chercher juste "Nom: Message"
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            parsed.append({
                                'date': '',
                                'heure': '',
                                'auteur': parts[0].strip(),
                                'texte': parts[1].strip()
                            })
            else:
                for date, heure, auteur, texte in all_matches:
                    texte_clean = texte.strip()
                    # Ignorer messages système
                    if len(texte_clean) > 0 and not texte_clean.startswith('<'):
                        parsed.append({
                            'date': date,
                            'heure': heure,
                            'auteur': auteur.strip(),
                            'texte': texte_clean
                        })

            logger.info(f"Messages parsés: {len(parsed)}")

            # Debug: afficher premiers messages
            if parsed:
                logger.info(f"Exemple premier message: {parsed[0]}")
            else:
                logger.warning(f"Contenu fichier (200 premiers chars): {content[:200]}")

            return parsed, "OK"

        except Exception as e:
            logger.error(f"Erreur parsing messages: {e}")
            return [], str(e)

    @staticmethod
    def extraire_produits_ia(messages, api_key):
        """Extraire les produits via Gemini"""
        if not GEMINI_AVAILABLE:
            return [], "Module google-generativeai non installé"

        try:
            # Configurer Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Préparer le contexte
            messages_texte = "\n".join([
                f"{m['auteur']}: {m['texte']}" for m in messages[:200]  # Limiter à 200 messages
            ])

            prompt = f"""
Tu es un assistant d'extraction de données pour un système de gestion de boutique au Bénin.

Analyse ces messages WhatsApp et extrais UNIQUEMENT les produits mentionnés avec leurs informations.

RÈGLES STRICTES:
1. Prix en FCFA (cherche: "F", "FCFA", "CFA", nombres suivis de ces termes)
2. Si code-barres mentionné (13 chiffres), l'inclure
3. Ne pas inventer de données
4. Ignorer messages non-produits (salutations, questions, etc.)
5. Format JSON strict

MESSAGES:
{messages_texte}

RETOURNE UNIQUEMENT un JSON valide:
{{
  "produits": [
    {{
      "nom": "Nom exact du produit",
      "prix": 1000,
      "description": "Description si disponible",
      "code_barre": "1234567890123",
      "categorie_suggeree": "Catégorie probable",
      "confiance": 0.95
    }}
  ]
}}

Si aucun produit trouvé, retourne: {{"produits": []}}
"""

            response = model.generate_content(prompt)
            text = response.text.strip()

            # Nettoyer la réponse (enlever markdown si présent)
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parser JSON
            data = json.loads(text)
            produits = data.get('produits', [])

            logger.info(f"Produits extraits: {len(produits)}")
            return produits, "OK"

        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return [], f"Erreur JSON: {e}"
        except Exception as e:
            logger.error(f"Erreur Gemini: {e}")
            return [], str(e)

    @staticmethod
    def detecter_type_code_barre(code):
        """Détecter le type de code-barre"""
        if not code:
            return None

        code = str(code).strip()

        # EAN-13
        if len(code) == 13 and code.isdigit():
            checksum = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) == checksum:
                return 'ean13'

        # EAN-8
        if len(code) == 8 and code.isdigit():
            checksum = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) == checksum:
                return 'ean8'

        return 'code128'

    @staticmethod
    def nettoyer_temp(temp_dir):
        """Nettoyer le répertoire temporaire"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Erreur nettoyage temp: {e}")

    @staticmethod
    def traiter_export_whatsapp(zip_path, api_key=None, temp_dir=None):
        """
        Traiter un export WhatsApp complet

        Returns: (produits_extraits, erreur)
        """
        if temp_dir is None:
            temp_dir = f"/tmp/whatsapp_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Extraire ZIP
            messages_file, images, err = IAExtraction.extraire_zip_whatsapp(zip_path, temp_dir)
            if not messages_file:
                return [], err

            # Parser messages
            messages, err = IAExtraction.parser_messages_whatsapp(messages_file)
            if not messages:
                return [], err

            # Extraire produits (basique par défaut, IA si clé fournie)
            if api_key and GEMINI_AVAILABLE:
                produits, err = IAExtraction.extraire_produits_ia(messages, api_key)
                if err != "OK":
                    logger.warning(f"Échec IA, fallback parser basique: {err}")
                    produits = IAExtraction.parser_basique_sans_ia(messages)
            else:
                logger.info("Parser basique activé (pas de clé API)")
                produits = IAExtraction.parser_basique_sans_ia(messages)

            # Enrichir avec détection type code-barre
            for produit in produits:
                code = produit.get('code_barre')
                if code:
                    type_code = IAExtraction.detecter_type_code_barre(code)
                    produit['type_code_barre'] = type_code
                else:
                    produit['type_code_barre'] = 'code128'

            return produits, "OK"

        finally:
            # Nettoyer
            IAExtraction.nettoyer_temp(temp_dir)

    @staticmethod
    def parser_basique_sans_ia(messages):
        """
        Parser basique sans IA (fallback)
        Cherche patterns simples: Nom + Prix
        """
        produits = []
        produits_dict = {}  # Pour éviter doublons

        # Patterns simples
        # Ex: "Savon Lux 500F", "Riz 25kg 12000 FCFA"
        pattern_prix = r'(\d+)\s*(?:F|FCFA|CFA|fr?)'

        for msg in messages:
            texte = msg['texte']

            # Ignorer messages système ou trop courts
            if len(texte) < 5:
                continue

            # Chercher prix
            matches = re.findall(pattern_prix, texte, re.IGNORECASE)
            if not matches:
                continue

            # Extraire le prix le plus probable (souvent le premier ou le plus grand)
            prix_trouve = max([int(m) for m in matches])

            # Extraire le nom (texte avant le premier prix)
            pattern_search = rf'(.+?)\s*{prix_trouve}\s*(?:F|FCFA|CFA|fr?)'
            match = re.search(pattern_search, texte, re.IGNORECASE)

            if match:
                nom = match.group(1).strip()
                # Nettoyer le nom
                nom = re.sub(r'^[-•*\s]+', '', nom)  # Enlever puces
                nom = re.sub(r'[:\s]+$', '', nom)    # Enlever : finaux

                # Valider le nom
                if len(nom) > 3 and len(nom) < 100:
                    # Éviter doublons (même nom)
                    if nom.lower() not in produits_dict:
                        produits_dict[nom.lower()] = {
                            'nom': nom,
                            'prix': prix_trouve,
                            'description': '',
                            'code_barre': None,
                            'categorie_suggeree': 'Non catégorisé',
                            'confiance': 0.6,
                            'type_code_barre': 'code128'
                        }

        produits = list(produits_dict.values())
        logger.info(f"Parser basique: {len(produits)} produits extraits")
        return produits
