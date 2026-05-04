"""
Prévisualisation du ticket thermique en texte pur.
Simule exactement ce qui sortira sur l'imprimante, sans hardware.
Usage : python scripts/preview_ticket.py [vente_id]
"""
import sys
import os

# Ajouter la racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from datetime import datetime

LARGEURS = {'58mm': 32, '80mm': 48}

def ligne(car, largeur):
    return car * largeur

def centrer(texte, largeur):
    return texte.center(largeur)

def droite(texte, largeur):
    return texte.rjust(largeur)

def preview_ticket(vente_id=None):
    from modules.ventes import Vente
    from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE

    # Prendre la dernière vente si pas d'ID fourni
    if vente_id is None:
        result = db.fetch_one("SELECT id FROM ventes ORDER BY id DESC LIMIT 1")
        if not result:
            print("Aucune vente trouvée dans la base de données.")
            return
        vente_id = result['id']

    vente = Vente.obtenir_vente(vente_id)
    if not vente:
        print(f"Vente {vente_id} introuvable.")
        return

    details = Vente.obtenir_details_vente(vente_id)
    if not details:
        print("Aucun détail pour cette vente.")
        return

    numero_vente = vente['numero_vente']
    date_vente   = vente['date_vente']
    total        = vente['total']
    client       = vente['client'] or ""

    nom_boutique  = db.get_parametre('boutique_nom', BOUTIQUE_NOM)
    adresse       = db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE)
    telephone     = db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE)
    ifu           = db.get_parametre('boutique_ifu', '')
    rccm          = db.get_parametre('boutique_rccm', '')
    message_pied  = db.get_parametre('recu_message_pied', '')
    format_papier = db.get_parametre('imprimante_format', '80mm')
    largeur       = LARGEURS.get(format_papier, 48)

    try:
        dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
        date_formatee = dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        date_formatee = date_vente

    ticket = []

    # Séparateur visuel
    ticket.append("┌" + "─" * largeur + "┐")

    # EN-TETE
    ticket.append("│" + centrer(f"*** {nom_boutique.upper()} ***", largeur) + "│")
    ticket.append("│" + centrer(adresse, largeur) + "│")
    ticket.append("│" + centrer(f"Tel: {telephone}", largeur) + "│")
    if ifu:
        ticket.append("│" + centrer(f"IFU: {ifu}", largeur) + "│")
    if rccm:
        ticket.append("│" + centrer(f"RCCM: {rccm}", largeur) + "│")
    ticket.append("│" + ligne('=', largeur) + "│")

    # INFOS VENTE
    ticket.append("│" + centrer(f"RECU N. {numero_vente}", largeur) + "│")
    ticket.append("│" + f"Date: {date_formatee}".ljust(largeur) + "│")
    if client:
        ticket.append("│" + f"Client: {client}".ljust(largeur) + "│")
    ticket.append("│" + ligne('-', largeur) + "│")

    # EN-TETE COLONNES
    if largeur >= 48:
        header = f"{'Article':<24}{'Qte':>4}{'P.U.':>9}{'Total':>11}"
    else:
        header = f"{'Article':<14}{'Qt':>3}{'P.U':>7}{'Tot':>8}"
    ticket.append("│" + header + "│")
    ticket.append("│" + ligne('-', largeur) + "│")

    # ARTICLES
    has_gros = False
    for detail in details:
        nom       = detail['nom']
        quantite  = detail['quantite']
        prix_unit = detail['prix_unitaire']
        sous_total = detail['sous_total']
        try:
            is_gros = bool(detail['is_prix_gros'])
        except Exception:
            is_gros = False
        if is_gros:
            has_gros = True

        if largeur >= 48:
            nom_court = nom[:23] if len(nom) > 23 else nom
            if is_gros:
                nom_court = nom_court + "*"
            ligne_article = f"{nom_court:<24}{quantite:>4}{prix_unit:>9,.0f}{sous_total:>11,.0f}"
        else:
            nom_court = nom[:13] if len(nom) > 13 else nom
            if is_gros:
                nom_court = nom_court + "*"
            ligne_article = f"{nom_court:<14}{quantite:>3}{prix_unit:>7,.0f}{sous_total:>8,.0f}"
        ticket.append("│" + ligne_article + "│")

    if has_gros:
        ticket.append("│" + "* Prix gros applique".ljust(largeur) + "│")

    ticket.append("│" + ligne('=', largeur) + "│")

    try:
        remise = float(vente['remise'] or 0)
    except Exception:
        remise = 0

    # REMISE
    if remise > 0:
        ticket.append("│" + f"Sous-total: {total + remise:,.0f} FCFA".rjust(largeur) + "│")
        ticket.append("│" + f"Remise: -{remise:,.0f} FCFA".rjust(largeur) + "│")
        ticket.append("│" + ligne('-', largeur) + "│")

    # TVA
    try:
        from modules.fiscalite import Fiscalite
        if Fiscalite.tva_active():
            decomp = Fiscalite.calculer_tva(total)
            ticket.append("│" + f"Sous-total HT: {decomp['ht']:,.0f} FCFA".rjust(largeur) + "│")
            ticket.append("│" + f"TVA ({decomp['taux']:.0f}%): {decomp['tva']:,.0f} FCFA".rjust(largeur) + "│")
            ticket.append("│" + ligne('-', largeur) + "│")
    except Exception:
        pass

    # TOTAL
    total_txt = f"TOTAL: {total:,.0f} FCFA"
    ticket.append("│" + f">>> {total_txt} <<<".rjust(largeur) + "│")

    # PAIEMENTS
    try:
        paiements = db.fetch_all(
            "SELECT mode, montant, montant_recu, monnaie_rendue, reference FROM paiements WHERE vente_id = ?",
            (vente_id,)
        )
        if paiements:
            ticket.append("│" + ligne('-', largeur) + "│")
            mode_labels = {
                'especes': 'Especes',
                'orange_money': 'Orange Money',
                'mtn_momo': 'MTN MoMo',
                'moov_money': 'Moov Money',
                'wave': 'Wave Money',
                'mobile_money': 'Mobile Money',
                'carte': 'Carte bancaire',
                'virement': 'Virement',
                'cheque': 'Cheque',
            }
            for p in paiements:
                mode_key = p['mode']
                mode_label = mode_labels.get(mode_key, mode_key)
                # Extraire l'opérateur depuis la référence [MTN MoMo]...
                ref = p['reference'] or ''
                if ref.startswith('['):
                    end = ref.find(']')
                    if end > 0:
                        mode_label = ref[1:end]
                        ref = ref[end+1:].strip()
                ticket.append("│" + f"Paiement: {mode_label}".ljust(largeur) + "│")
                if mode_key == 'especes' and p['montant_recu'] and p['monnaie_rendue']:
                    ticket.append("│" + f"Recu: {p['montant_recu']:,.0f} FCFA".ljust(largeur) + "│")
                    ticket.append("│" + f"** Monnaie: {p['monnaie_rendue']:,.0f} FCFA **".ljust(largeur) + "│")
                if ref:
                    ticket.append("│" + f"Ref: {ref}".ljust(largeur) + "│")
    except Exception as e:
        ticket.append("│" + f"[paiements: {e}]".ljust(largeur) + "│")

    # FOOTER
    ticket.append("│" + ligne(' ', largeur) + "│")
    ticket.append("│" + centrer("[QR CODE]", largeur) + "│")
    ticket.append("│" + ligne(' ', largeur) + "│")
    ticket.append("│" + centrer("Merci pour votre confiance !", largeur) + "│")
    if message_pied:
        ticket.append("│" + ligne('-', largeur) + "│")
        ticket.append("│" + centrer(message_pied, largeur) + "│")
    ticket.append("│" + centrer(nom_boutique, largeur) + "│")
    ticket.append("└" + "─" * largeur + "┘")
    ticket.append(f"\n  Format: {format_papier} ({largeur} caractères/ligne)")
    ticket.append(f"  Vente ID: {vente_id} | Numéro: {numero_vente}")

    print("\n".join(ticket))

    # Sauvegarder dans un fichier
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ticket_preview.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ticket))
    print(f"\n  → Sauvegardé dans : {output_path}")


if __name__ == '__main__':
    vente_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    preview_ticket(vente_id)
