"""
Gestionnaire de mises à jour via GitHub Releases API
Fonctionne avec repos privés et publics
"""
import requests
import webbrowser
from packaging import version as pkg_version
from modules.logger import get_logger

logger = get_logger('updater')

# GitHub Releases API (fonctionne même avec repo privé)
GITHUB_OWNER = "TIDJANI12345"
GITHUB_REPO = "gestion-boutique"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Timeout adapté aux réseaux africains (en secondes)
TIMEOUT_VERIFICATION = 10
RETRY_ATTEMPTS = 2


class Updater:
    """Gestionnaire de vérification et téléchargement des mises à jour"""

    @staticmethod
    def verifier_mise_a_jour(version_actuelle):
        """
        Vérifier si une nouvelle version est disponible via GitHub Releases

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

                response = requests.get(
                    RELEASES_API,
                    timeout=TIMEOUT_VERIFICATION,
                    headers={
                        'Accept': 'application/vnd.github.v3+json',
                        'Cache-Control': 'no-cache'
                    }
                )
                response.raise_for_status()

                release = response.json()
                remote_info = Updater._parser_release(release)
                remote_version = remote_info.get('version', '0.0.0')

                logger.info(f"Version actuelle: {version_actuelle}, Version distante: {remote_version}")

                if pkg_version.parse(remote_version) > pkg_version.parse(version_actuelle):
                    logger.info(f"Nouvelle version disponible : {remote_version}")
                    return True, remote_info
                else:
                    logger.info("Application à jour")
                    return False, None

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout (tentative {tentative + 1}/{RETRY_ATTEMPTS})")
                if tentative < RETRY_ATTEMPTS - 1:
                    continue
                return False, None

            except requests.exceptions.ConnectionError:
                logger.warning("Pas de connexion internet")
                return False, None

            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 404:
                    logger.info("Aucune release trouvée sur GitHub")
                else:
                    logger.error(f"Erreur HTTP : {e}")
                return False, None

            except Exception as e:
                logger.error(f"Erreur inattendue : {e}")
                return False, None

        return False, None

    @staticmethod
    def _parser_release(release):
        """
        Convertir la réponse GitHub Releases API en format interne

        Args:
            release (dict): Réponse JSON de l'API GitHub

        Returns:
            dict: Format compatible avec le système de notification
        """
        # Extraire la version du tag (ex: "v2.1.0" → "2.1.0")
        tag = release.get('tag_name', '0.0.0')
        version = tag.lstrip('vV')

        # Date de publication
        published = release.get('published_at', '')
        date = published[:10] if published else ''

        # URL de la page release (pour voir les notes)
        html_url = release.get('html_url', '')

        # Chercher l'exe dans les assets
        url_download = html_url  # Fallback sur la page release
        taille_mb = 0

        assets = release.get('assets', [])
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') or name.endswith('.zip') or name.endswith('.msi'):
                url_download = asset.get('browser_download_url', html_url)
                taille_bytes = asset.get('size', 0)
                taille_mb = round(taille_bytes / (1024 * 1024))
                break

        # Corps de la release (notes de version)
        body = release.get('body', '')
        message = body[:200] if body else release.get('name', '')

        # Détecter si critique (chercher mot-clé dans le titre ou body)
        name = release.get('name', '').lower()
        critique = 'critique' in name or 'critical' in name or 'urgent' in name or release.get('prerelease', False) is False and 'security' in body.lower()

        return {
            'version': version,
            'date': date,
            'url_download': url_download,
            'url_changelog': html_url,
            'taille_mb': taille_mb if taille_mb > 0 else None,
            'critique': critique,
            'message': message,
        }

    @staticmethod
    def ouvrir_page_telechargement(url):
        """Ouvrir le navigateur pour télécharger la mise à jour"""
        try:
            logger.info(f"Ouverture du navigateur : {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Erreur ouverture navigateur : {e}")

    @staticmethod
    def ignorer_version(version_a_ignorer):
        """Marquer une version comme ignorée"""
        try:
            from database import db
            db.set_parametre('version_ignoree', version_a_ignorer)
            logger.info(f"Version {version_a_ignorer} marquée comme ignorée")
        except Exception as e:
            logger.error(f"Erreur : {e}")

    @staticmethod
    def est_ignoree(version_remote):
        """Vérifier si l'utilisateur a choisi d'ignorer cette version"""
        try:
            from database import db
            version_ignoree = db.get_parametre('version_ignoree', '')
            return version_ignoree == version_remote
        except Exception as e:
            logger.error(f"Erreur : {e}")
            return False

    @staticmethod
    def reinitialiser_versions_ignorees():
        """Réinitialiser les versions ignorées"""
        try:
            from database import db
            db.set_parametre('version_ignoree', '')
            logger.info("Versions ignorées réinitialisées")
        except Exception as e:
            logger.error(f"Erreur : {e}")


def formater_taille(taille_mb):
    """Formater la taille en MB de manière lisible"""
    if taille_mb is None:
        return ""
    if taille_mb < 1:
        return f"{taille_mb * 1024:.0f} KB"
    elif taille_mb >= 1024:
        return f"{taille_mb / 1024:.1f} GB"
    else:
        return f"{taille_mb:.0f} MB"
