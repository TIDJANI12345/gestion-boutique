"""
Module d'impression thermique ESC/POS
Support imprimantes 58mm et 80mm
"""
from modules.logger import get_logger
from database import db

logger = get_logger('imprimante')

# Import conditionnel - l'imprimante thermique est optionnelle
try:
    from escpos.printer import Usb, Network, Serial
    ESCPOS_DISPONIBLE = True
except ImportError:
    ESCPOS_DISPONIBLE = False
    logger.warning("python-escpos non installe - impression thermique indisponible")

try:
    import qrcode
    QRCODE_DISPONIBLE = True
except ImportError:
    QRCODE_DISPONIBLE = False


# Largeurs en caracteres selon le format papier
LARGEURS = {
    '58mm': 32,
    '80mm': 48,
}


class ImprimanteThermique:
    """Gestion de l'impression thermique ESC/POS"""

    @staticmethod
    def est_disponible():
        """Verifier si l'impression thermique est possible"""
        return ESCPOS_DISPONIBLE

    @staticmethod
    def _connecter():
        """Connecter a l'imprimante selon la configuration"""
        if not ESCPOS_DISPONIBLE:
            return None

        mode = db.get_parametre('imprimante_mode', 'usb')
        try:
            if mode == 'usb':
                vendor_id = int(db.get_parametre('imprimante_usb_vendor', '0x0'), 16)
                product_id = int(db.get_parametre('imprimante_usb_product', '0x0'), 16)
                if vendor_id and product_id:
                    return Usb(vendor_id, product_id)
            elif mode == 'reseau':
                ip = db.get_parametre('imprimante_ip', '')
                port = int(db.get_parametre('imprimante_port', '9100'))
                if ip:
                    return Network(ip, port)
            elif mode == 'serie':
                port = db.get_parametre('imprimante_serie_port', 'COM1')
                baudrate = int(db.get_parametre('imprimante_serie_baudrate', '9600'))
                return Serial(port, baudrate=baudrate)
        except Exception as e:
            logger.error(f"Connexion imprimante echouee ({mode}): {e}")
        return None

    @staticmethod
    def _centrer(texte, largeur):
        """Centrer un texte sur la largeur du ticket"""
        return texte.center(largeur)

    @staticmethod
    def _ligne(caractere, largeur):
        """Ligne de separation"""
        return caractere * largeur

    @staticmethod
    def imprimer_recu(vente_id):
        """Imprimer un recu sur imprimante thermique"""
        from modules.ventes import Vente
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE

        if not ESCPOS_DISPONIBLE:
            return False, "python-escpos n'est pas installe"

        printer = ImprimanteThermique._connecter()
        if not printer:
            return False, "Impossible de se connecter a l'imprimante"

        try:
            vente = Vente.obtenir_vente(vente_id)
            if not vente:
                return False, "Vente introuvable"

            details = Vente.obtenir_details_vente(vente_id)
            if not details:
                return False, "Aucun detail de vente"

            numero_vente = vente['numero_vente']
            date_vente = vente['date_vente']
            total = vente['total']
            client = vente['client'] if vente['client'] else ""

            # Infos boutique
            nom_boutique = db.get_parametre('boutique_nom', BOUTIQUE_NOM)
            adresse = db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE)
            telephone = db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE)

            format_papier = db.get_parametre('imprimante_format', '80mm')
            largeur = LARGEURS.get(format_papier, 48)

            # === EN-TETE ===
            printer.set(align='center', bold=True, double_height=True, double_width=True)
            printer.text(f"{nom_boutique}\n")

            printer.set(align='center', bold=False, double_height=False, double_width=False)
            printer.text(f"{adresse}\n")
            printer.text(f"Tel: {telephone}\n")
            printer.text(ImprimanteThermique._ligne('=', largeur) + "\n")

            # === INFOS VENTE ===
            printer.set(align='center', bold=True)
            printer.text(f"RECU N. {numero_vente}\n")

            printer.set(align='left', bold=False)
            # Formater la date
            try:
                from datetime import datetime
                dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
                date_formatee = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_formatee = date_vente

            printer.text(f"Date: {date_formatee}\n")
            if client:
                printer.text(f"Client: {client}\n")
            printer.text(ImprimanteThermique._ligne('-', largeur) + "\n")

            # === ARTICLES ===
            printer.set(align='left', bold=True)
            # En-tete colonnes
            if largeur >= 48:
                header = f"{'Article':<24}{'Qte':>4}{'P.U.':>9}{'Total':>11}"
            else:
                header = f"{'Article':<14}{'Qt':>3}{'P.U':>7}{'Tot':>8}"
            printer.text(header + "\n")
            printer.text(ImprimanteThermique._ligne('-', largeur) + "\n")

            printer.set(align='left', bold=False)
            for detail in details:
                nom = detail['nom']
                quantite = detail['quantite']
                prix_unit = detail['prix_unitaire']
                sous_total = detail['sous_total']

                if largeur >= 48:
                    # Tronquer le nom si trop long
                    nom_court = nom[:24] if len(nom) > 24 else nom
                    ligne = f"{nom_court:<24}{quantite:>4}{prix_unit:>9,.0f}{sous_total:>11,.0f}"
                else:
                    nom_court = nom[:14] if len(nom) > 14 else nom
                    ligne = f"{nom_court:<14}{quantite:>3}{prix_unit:>7,.0f}{sous_total:>8,.0f}"
                printer.text(ligne + "\n")

            printer.text(ImprimanteThermique._ligne('=', largeur) + "\n")

            # === TVA (si active) ===
            try:
                from modules.fiscalite import Fiscalite
                if Fiscalite.tva_active():
                    decomp = Fiscalite.calculer_tva(total)
                    printer.set(align='right', bold=False, double_height=False)
                    printer.text(f"Sous-total HT: {decomp['ht']:,.0f} FCFA\n")
                    printer.text(f"TVA ({decomp['taux']:.0f}%): {decomp['tva']:,.0f} FCFA\n")
                    printer.text(ImprimanteThermique._ligne('-', largeur) + "\n")
            except Exception:
                pass

            # === TOTAL ===
            printer.set(align='right', bold=True, double_height=True)
            printer.text(f"TOTAL: {total:,.0f} FCFA\n")

            # === PAIEMENT ===
            printer.set(align='left', bold=False, double_height=False)
            # Chercher les infos de paiement si la table existe
            try:
                paiements = db.fetch_all(
                    "SELECT mode, montant, montant_recu, monnaie_rendue, reference FROM paiements WHERE vente_id = ?",
                    (vente_id,)
                )
                if paiements:
                    printer.text(ImprimanteThermique._ligne('-', largeur) + "\n")
                    for p in paiements:
                        mode_labels = {
                            'especes': 'Especes',
                            'orange_money': 'Orange Money',
                            'mtn_momo': 'MTN MoMo',
                            'moov_money': 'Moov Money',
                        }
                        mode_label = mode_labels.get(p['mode_paiement'], p['mode_paiement'])
                        printer.text(f"Paiement: {mode_label}\n")
                        if p['mode_paiement'] == 'especes' and p['montant_recu'] and p['monnaie_rendue']:
                            printer.text(f"Recu: {p['montant_recu']:,.0f} FCFA\n")
                            printer.set(bold=True)
                            printer.text(f"Monnaie: {p['monnaie_rendue']:,.0f} FCFA\n")
                            printer.set(bold=False)
                        if p['reference']:
                            printer.text(f"Ref: {p['reference']}\n")
            except Exception:
                pass  # Table paiements n'existe peut-etre pas encore

            # === QR CODE ===
            if QRCODE_DISPONIBLE:
                printer.text("\n")
                try:
                    printer.qr(numero_vente, size=6, center=True)
                except Exception as e:
                    logger.warning(f"QR code impression echouee: {e}")

            # === FOOTER ===
            printer.text("\n")
            printer.set(align='center', bold=False)
            printer.text("Merci pour votre confiance !\n")
            printer.text(f"{nom_boutique}\n")
            printer.text("\n\n\n")

            # Couper le papier
            try:
                printer.cut()
            except Exception:
                pass

            printer.close()
            logger.info(f"Ticket imprime pour vente {numero_vente}")
            return True, "Ticket imprime avec succes"

        except Exception as e:
            logger.error(f"Erreur impression: {e}")
            try:
                printer.close()
            except Exception:
                pass
            return False, f"Erreur d'impression: {e}"

    @staticmethod
    def imprimer_test():
        """Imprimer un ticket de test"""
        if not ESCPOS_DISPONIBLE:
            return False, "python-escpos n'est pas installe"

        printer = ImprimanteThermique._connecter()
        if not printer:
            return False, "Impossible de se connecter a l'imprimante"

        try:
            nom_boutique = db.get_parametre('boutique_nom', 'Ma Boutique')
            format_papier = db.get_parametre('imprimante_format', '80mm')
            largeur = LARGEURS.get(format_papier, 48)

            printer.set(align='center', bold=True, double_height=True, double_width=True)
            printer.text(f"{nom_boutique}\n")

            printer.set(align='center', bold=False, double_height=False, double_width=False)
            printer.text(ImprimanteThermique._ligne('=', largeur) + "\n")
            printer.text("TEST D'IMPRESSION\n")
            printer.text(ImprimanteThermique._ligne('=', largeur) + "\n")
            printer.text(f"Format: {format_papier}\n")
            printer.text(f"Largeur: {largeur} caracteres\n")

            from datetime import datetime
            printer.text(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

            if QRCODE_DISPONIBLE:
                printer.text("\n")
                printer.qr("TEST-IMPRESSION", size=6, center=True)

            printer.text("\nImprimante OK !\n\n\n")
            try:
                printer.cut()
            except Exception:
                pass

            printer.close()
            return True, "Test d'impression reussi"

        except Exception as e:
            try:
                printer.close()
            except Exception:
                pass
            return False, f"Erreur test: {e}"
