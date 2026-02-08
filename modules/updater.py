"""
Gestionnaire de mises à jour automatique
Vérifie la disponibilité de nouvelles versions et gère les notifications
"""
import requests
import webbrowser
from packaging import version as pkg_version
from modules.logger import get_logger

logger = get_logger('updater')

# URL du fichier version.json hébergé en ligne
# À MODIFIER après upload sur GitHub Releases ou autre serveur
UPDATE_URL = "https://raw.githubusercontent.com/TIDJANI12345/gestion-boutique/main/version.json"

# Timeout adapté aux réseaux africains (en secondes)
TIMEOUT_VERIFICATION = 10  # 10 secondes pour vérification
RETRY_ATTEMPTS = 2         # Nombre de tentatives


class Updater:
    """Gestionnaire de vérification et téléchargement des mises à jour"""

    @staticmethod
    def verifier_mise_a_jour(version_actuelle):
        """
        Vérifier si une nouvelle version est disponible

        Args:
            version_actuelle (str): Version actuelle de l'app (ex: "2.0.0")

        Returns:
            tuple: (bool, dict ou None)
                - bool: True si nouvelle version disponible
                - dict: Informations de la nouvelle version ou None
        """
        for tentative in range(RETRY_ATTEMPTS):
            try:
                logger.info(f"Vérification des mises à jour (tentative {tentative + 1}/{RETRY_ATTEMPTS})...")

                # Requête HTTP légère (quelques KB seulement)
                response = requests.get(
                    UPDATE_URL,
                    timeout=TIMEOUT_VERIFICATION,
                    headers={'Cache-Control': 'no-cache'}
                )
                response.raise_for_status()

                # Parser les informations de version
                remote_info = response.json()
                remote_version = remote_info.get('version', '0.0.0')

                logger.info(f"Version actuelle: {version_actuelle}, Version distante: {remote_version}")

                # Comparer les versions (gère format sémantique x.y.z)
                if pkg_version.parse(remote_version) > pkg_version.parse(version_actuelle):
                    logger.info(f"✅ Nouvelle version disponible : {remote_version}")
                    return True, remote_info
                else:
                    logger.info("✅ Application à jour")
                    return False, None

            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout lors de la vérification (tentative {tentative + 1}/{RETRY_ATTEMPTS})")
                if tentative < RETRY_ATTEMPTS - 1:
                    continue
                else:
                    logger.warning("❌ Impossible de vérifier les MAJ (timeout)")
                    return False, None

            except requests.exceptions.ConnectionError:
                logger.warning("❌ Pas de connexion internet pour vérifier les MAJ")
                return False, None

            except requests.exceptions.HTTPError as e:
                logger.error(f"❌ Erreur HTTP lors de la vérification : {e}")
                return False, None

            except ValueError as e:
                logger.error(f"❌ Erreur de parsing JSON : {e}")
                return False, None

            except Exception as e:
                logger.error(f"❌ Erreur inattendue lors de la vérification : {e}")
                return False, None

        return False, None

    @staticmethod
    def ouvrir_page_telechargement(url):
        """
        Ouvrir le navigateur par défaut pour télécharger la mise à jour

        Args:
            url (str): URL de téléchargement de la nouvelle version
        """
        try:
            logger.info(f"Ouverture du navigateur : {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Erreur ouverture navigateur : {e}")

    @staticmethod
    def ignorer_version(version_a_ignorer):
        """
        Marquer une version comme ignorée par l'utilisateur
        La notification ne sera plus affichée pour cette version

        Args:
            version_a_ignorer (str): Version à ignorer (ex: "2.1.0")
        """
        try:
            from database import db
            db.set_parametre('version_ignoree', version_a_ignorer)
            logger.info(f"Version {version_a_ignorer} marquée comme ignorée")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la version ignorée : {e}")

    @staticmethod
    def est_ignoree(version_remote):
        """
        Vérifier si l'utilisateur a choisi d'ignorer cette version

        Args:
            version_remote (str): Version à vérifier

        Returns:
            bool: True si version ignorée, False sinon
        """
        try:
            from database import db
            version_ignoree = db.get_parametre('version_ignoree', '')
            return version_ignoree == version_remote
        except Exception as e:
            logger.error(f"Erreur lors de la vérification version ignorée : {e}")
            return False

    @staticmethod
    def reinitialiser_versions_ignorees():
        """Réinitialiser les versions ignorées (pour forcer la notification)"""
        try:
            from database import db
            db.set_parametre('version_ignoree', '')
            logger.info("Versions ignorées réinitialisées")
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation : {e}")


def formater_taille(taille_mb):
    """
    Formater la taille en MB de manière lisible

    Args:
        taille_mb (int ou float): Taille en mégaoctets

    Returns:
        str: Taille formatée (ex: "105 MB" ou "1.2 GB")
    """
    if taille_mb < 1:
        return f"{taille_mb * 1024:.0f} KB"
    elif taille_mb >= 1024:
        return f"{taille_mb / 1024:.1f} GB"
    else:
        return f"{taille_mb:.0f} MB"
