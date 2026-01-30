"""
Module de sauvegarde et restauration
"""
import os
import shutil
import zipfile
import threading
from datetime import datetime
import config
from modules.logger import get_logger

logger = get_logger('sauvegarde')

BACKUP_DIR = os.path.join(config.BASE_DIR, 'sauvegardes')
MAX_BACKUPS = 10


def _assurer_dossier_backup():
    """Creer le dossier de sauvegardes s'il n'existe pas"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)


def sauvegarder_locale():
    """Sauvegarder la base de donnees avec timestamp.
    Garde les N dernieres sauvegardes (defaut 10).

    Returns: (succes, message, chemin)
    """
    try:
        _assurer_dossier_backup()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"boutique_{timestamp}.db")

        shutil.copy2(config.DB_PATH, backup_file)
        logger.info(f"Sauvegarde locale creee: {backup_file}")

        # Nettoyage des anciennes sauvegardes
        _nettoyer_anciennes_sauvegardes()

        return True, "Sauvegarde creee avec succes", backup_file

    except Exception as e:
        logger.error(f"Erreur sauvegarde locale: {e}")
        return False, f"Erreur: {e}", None


def _nettoyer_anciennes_sauvegardes():
    """Supprimer les sauvegardes au-dela de MAX_BACKUPS"""
    try:
        sauvegardes = lister_sauvegardes()
        if len(sauvegardes) > MAX_BACKUPS:
            # Les sauvegardes sont triees par date decroissante
            a_supprimer = sauvegardes[MAX_BACKUPS:]
            for s in a_supprimer:
                try:
                    os.remove(s['chemin'])
                    logger.info(f"Ancienne sauvegarde supprimee: {s['chemin']}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {s['chemin']}: {e}")
    except Exception as e:
        logger.warning(f"Erreur nettoyage sauvegardes: {e}")


def lister_sauvegardes():
    """Retourner la liste des sauvegardes disponibles.

    Returns: liste de dicts {nom, chemin, date, taille}
    """
    _assurer_dossier_backup()
    sauvegardes = []

    for fichier in os.listdir(BACKUP_DIR):
        if fichier.endswith('.db'):
            chemin = os.path.join(BACKUP_DIR, fichier)
            stat = os.stat(chemin)
            taille_mo = stat.st_size / (1024 * 1024)

            # Extraire la date du nom du fichier
            try:
                # Format: boutique_YYYYMMDD_HHMMSS.db
                parts = fichier.replace('.db', '').split('_')
                if len(parts) >= 3:
                    date_str = f"{parts[1]}_{parts[2]}"
                    date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    date_affichage = date.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    date_affichage = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
                    date = datetime.fromtimestamp(stat.st_mtime)
            except Exception:
                date = datetime.fromtimestamp(stat.st_mtime)
                date_affichage = date.strftime("%d/%m/%Y %H:%M:%S")

            sauvegardes.append({
                'nom': fichier,
                'chemin': chemin,
                'date': date,
                'date_affichage': date_affichage,
                'taille': f"{taille_mo:.2f} Mo",
            })

    # Trier par date decroissante
    sauvegardes.sort(key=lambda x: x['date'], reverse=True)
    return sauvegardes


def restaurer(chemin_backup):
    """Restaurer la base de donnees a partir d'une sauvegarde.

    Returns: (succes, message)
    """
    if not os.path.exists(chemin_backup):
        return False, "Fichier de sauvegarde introuvable"

    try:
        from database import db

        # Sauvegarder la base actuelle avant restauration
        sauvegarder_locale()

        # Fermer la connexion
        db.close()

        # Remplacer le fichier
        shutil.copy2(chemin_backup, config.DB_PATH)

        # Rouvrir la connexion
        db.connect()
        db.create_tables()

        logger.info(f"Restauration reussie depuis: {chemin_backup}")
        return True, "Restauration reussie! L'application va se recharger."

    except Exception as e:
        logger.error(f"Erreur restauration: {e}")
        # Tenter de reconnecter
        try:
            from database import db
            db.connect()
        except Exception:
            pass
        return False, f"Erreur de restauration: {e}"


def exporter_zip():
    """Exporter la base de donnees + images + recus dans un fichier ZIP.

    Returns: (succes, message, chemin_zip)
    """
    try:
        _assurer_dossier_backup()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(BACKUP_DIR, f"export_{timestamp}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Base de donnees
            if os.path.exists(config.DB_PATH):
                zf.write(config.DB_PATH, os.path.join('data', 'boutique.db'))

            # Images
            if os.path.exists(config.IMAGES_DIR):
                for fichier in os.listdir(config.IMAGES_DIR):
                    chemin = os.path.join(config.IMAGES_DIR, fichier)
                    if os.path.isfile(chemin):
                        zf.write(chemin, os.path.join('images', fichier))

            # Recus PDF
            if os.path.exists(config.RECUS_DIR):
                for fichier in os.listdir(config.RECUS_DIR):
                    chemin = os.path.join(config.RECUS_DIR, fichier)
                    if os.path.isfile(chemin):
                        zf.write(chemin, os.path.join('recus', fichier))

        logger.info(f"Export ZIP cree: {zip_path}")
        return True, "Export ZIP cree avec succes", zip_path

    except Exception as e:
        logger.error(f"Erreur export ZIP: {e}")
        return False, f"Erreur: {e}", None


def importer_zip(chemin_zip):
    """Importer un fichier ZIP (base de donnees + fichiers).

    Returns: (succes, message)
    """
    if not os.path.exists(chemin_zip):
        return False, "Fichier ZIP introuvable"

    try:
        from database import db

        # Verifier que c'est un ZIP valide
        if not zipfile.is_zipfile(chemin_zip):
            return False, "Le fichier n'est pas un ZIP valide"

        # Sauvegarder avant import
        sauvegarder_locale()

        with zipfile.ZipFile(chemin_zip, 'r') as zf:
            noms = zf.namelist()

            # Verifier que le ZIP contient une base de donnees
            db_dans_zip = any('boutique.db' in n for n in noms)
            if not db_dans_zip:
                return False, "Le ZIP ne contient pas de base de donnees"

            # Fermer la connexion avant remplacement
            db.close()

            # Extraire les fichiers
            for nom in noms:
                if nom.startswith('data/'):
                    dest = os.path.join(BASE_DIR, nom)
                elif nom.startswith('images/'):
                    dest = os.path.join(BASE_DIR, nom)
                elif nom.startswith('recus/'):
                    dest = os.path.join(BASE_DIR, nom)
                else:
                    continue

                # Creer les dossiers parents
                os.makedirs(os.path.dirname(dest), exist_ok=True)

                # Extraire le fichier
                with zf.open(nom) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())

            # Rouvrir la connexion
            db.connect()
            db.create_tables()

        logger.info(f"Import ZIP reussi depuis: {chemin_zip}")
        return True, "Import reussi! L'application va se recharger."

    except Exception as e:
        logger.error(f"Erreur import ZIP: {e}")
        try:
            from database import db
            db.connect()
        except Exception:
            pass
        return False, f"Erreur d'import: {e}"


def planifier_sauvegarde_auto():
    """Lancer la sauvegarde automatique en arriere-plan.
    Sauvegarde au demarrage, puis toutes les 24h.
    """
    def _boucle_sauvegarde():
        sauvegarder_locale()
        # Planifier la prochaine dans 24h
        timer = threading.Timer(86400, _boucle_sauvegarde)
        timer.daemon = True
        timer.start()

    # Demarrer dans un thread
    thread = threading.Thread(target=_boucle_sauvegarde, daemon=True)
    thread.start()
    logger.info("Sauvegarde automatique planifiee")
