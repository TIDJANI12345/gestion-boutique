"""
Module d'export WhatsApp - Version 2.0
Génération de messages formatés pour les revendeurs
"""
from datetime import datetime
from modules.produits import Produit
from database import db
from config import WHATSAPP_EMOJI_STYLES, EXPORTS_DIR
import os

class WhatsAppExport:
    
    @staticmethod
    def generer_message(options=None):
        """
        Générer un message WhatsApp formaté
        
        Options possibles:
        - titre: Titre du message
        - message_fin: Message de fin personnalisé
        - grouper_categories: Grouper par catégories (True/False)
        - afficher_stock: Afficher les stocks (True/False)
        - stock_min_only: Produits en stock uniquement (True/False)
        - inclure_prix_achat: Afficher prix d'achat (True/False)
        - emoji_style: Style d'emojis ('classic', 'modern', 'professional')
        - categories: Liste des catégories à inclure (None = toutes)
        """
        if options is None:
            options = {}
        
        # Options par défaut
        titre = options.get('titre', '🛒 PRODUITS DISPONIBLES')
        message_fin = options.get('message_fin', '')
        grouper_categories = options.get('grouper_categories', True)
        afficher_stock = options.get('afficher_stock', True)
        stock_min_only = options.get('stock_min_only', True)
        inclure_prix_achat = options.get('inclure_prix_achat', False)
        emoji_style = options.get('emoji_style', 'classic')
        categories_selectionnees = options.get('categories', None)
        
        # Emojis
        emojis = WHATSAPP_EMOJI_STYLES.get(emoji_style, WHATSAPP_EMOJI_STYLES['classic'])
        
        # Récupérer les infos boutique
        telephone = db.get_parametre('boutique_telephone', '+229 XX XX XX XX')
        nom_boutique = db.get_parametre('boutique_nom', 'Ma Boutique')
        
        # Construction du message
        message = []
        message.append(titre)
        message.append("─" * 30)
        message.append(f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        message.append("")
        
        # Récupérer les produits
        if grouper_categories:
            produits_par_categorie = Produit.obtenir_par_categorie()
            
            for categorie, produits in sorted(produits_par_categorie.items()):
                # Filtrer par catégories sélectionnées
                if categories_selectionnees and categorie not in categories_selectionnees:
                    continue
                
                # Filtrer les produits
                produits_filtres = []
                for p in produits:
                    if stock_min_only and p[5] <= 0:  # stock_actuel
                        continue
                    produits_filtres.append(p)
                
                if not produits_filtres:
                    continue
                
                # En-tête catégorie
                message.append(f"{emojis['category']} {categorie.upper()}")
                message.append("─" * 20)
                
                # Produits
                for produit in produits_filtres:
                    nom = produit[1]
                    prix_vente = produit[4]
                    stock = produit[5]
                    prix_achat = produit[3]
                    
                    message.append(f"{emojis['product']} *{nom}*")
                    message.append(f"   {emojis['price']} Prix : *{prix_vente:.0f} FCFA*")
                    
                    if inclure_prix_achat and prix_achat:
                        message.append(f"   💵 Prix achat : {prix_achat:.0f} FCFA")
                    
                    if afficher_stock:
                        message.append(f"   {emojis['stock']} Stock : {stock}")
                    
                    message.append("")
                
        else:
            # Sans groupement par catégories
            produits = Produit.obtenir_tous()
            
            for produit in produits:
                if stock_min_only and produit[5] <= 0:
                    continue
                
                categorie = produit[2]
                if categories_selectionnees and categorie not in categories_selectionnees:
                    continue
                
                nom = produit[1]
                prix_vente = produit[4]
                stock = produit[5]
                prix_achat = produit[3]
                
                message.append(f"{emojis['product']} *{nom}*")
                message.append(f"   {emojis['price']} Prix : *{prix_vente:.0f} FCFA*")
                
                if inclure_prix_achat and prix_achat:
                    message.append(f"   💵 Prix achat : {prix_achat:.0f} FCFA")
                
                if afficher_stock:
                    message.append(f"   {emojis['stock']} Stock : {stock}")
                
                message.append("")
        
        # Pied de page
        message.append("─" * 30)
        message.append(f"📞 Commander : {telephone}")
        
        if message_fin:
            message.append("")
            message.append(message_fin)
        
        message.append("")
        message.append("🙏 Merci pour votre confiance !")
        
        return "\n".join(message)
    
    @staticmethod
    def sauvegarder_export(message):
        """Sauvegarder le message dans un fichier"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"whatsapp_{timestamp}.txt"
            filepath = os.path.join(EXPORTS_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(message)
            
            print(f"✅ Export WhatsApp sauvegardé: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None
    
    @staticmethod
    def obtenir_apercu():
        """Générer un aperçu rapide du message"""
        options = {
            'titre': '🛒 PRODUITS DISPONIBLES',
            'grouper_categories': True,
            'afficher_stock': True,
            'stock_min_only': True,
            'emoji_style': 'classic'
        }
        return WhatsAppExport.generer_message(options)
