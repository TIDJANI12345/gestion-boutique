"""
Module de gestion des codes-barres - Version 2.0
Support Code128, EAN-13, EAN-8, Code39
"""
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os
from config import IMAGES_DIR, BARCODE_DEFAULT

class CodeBarre:
    
    @staticmethod
    def generer_image(code, nom_produit, prix, type_code='code128'):
        """
        Générer une image de code-barres avec informations
        """
        try:
            # Mapper les types
            type_mapping = {
                'code128': 'code128',
                'ean13': 'ean13',
                'ean8': 'ean8',
                'code39': 'code39',
            }
            
            barcode_type = type_mapping.get(type_code.lower(), 'code128')
            
            # Générer le code-barres
            code_barre_class = barcode.get_barcode_class(barcode_type)
            code_barre = code_barre_class(code, writer=ImageWriter())
            
            # Options pour le writer
            options = {
                'module_width': 0.3,
                'module_height': 10,
                'quiet_zone': 2,
                'font_size': 10,
                'text_distance': 3,
                'write_text': True
            }
            
            # Sauvegarder l'image
            chemin = os.path.join(IMAGES_DIR, code)
            filename = code_barre.save(chemin, options=options)
            
            # Ajouter le nom du produit et le prix sur l'image
            CodeBarre.ajouter_texte_sur_image(filename, nom_produit, prix)
            
            print(f"✅ Code-barres généré: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du code-barres: {e}")
            return None
    
    @staticmethod
    def ajouter_texte_sur_image(chemin_image, nom_produit, prix):
        """
        Ajouter le nom du produit et le prix sur l'image du code-barres
        """
        try:
            img = Image.open(chemin_image)
            width, height = img.size
            
            # Créer une nouvelle image plus grande
            nouvelle_hauteur = height + 60
            nouvelle_img = Image.new('RGB', (width, nouvelle_hauteur), 'white')
            
            # Coller l'image du code-barres
            nouvelle_img.paste(img, (0, 0))
            
            # Ajouter le texte
            draw = ImageDraw.Draw(nouvelle_img)
            
            # Essayer d'utiliser une police, sinon utiliser la police par défaut
            try:
                font = ImageFont.truetype("arial.ttf", 14)
                font_prix = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
                font_prix = ImageFont.load_default()
            
            # Nom du produit (tronquer si trop long)
            if len(nom_produit) > 30:
                nom_produit = nom_produit[:27] + "..."
            
            # Calculer la position du texte (centré)
            try:
                bbox_nom = draw.textbbox((0, 0), nom_produit, font=font)
                text_width_nom = bbox_nom[2] - bbox_nom[0]
            except:
                text_width_nom = len(nom_produit) * 8
            
            x_nom = (width - text_width_nom) // 2
            
            prix_text = f"Prix: {prix:.0f} FCFA"
            try:
                bbox_prix = draw.textbbox((0, 0), prix_text, font=font_prix)
                text_width_prix = bbox_prix[2] - bbox_prix[0]
            except:
                text_width_prix = len(prix_text) * 10
            
            x_prix = (width - text_width_prix) // 2
            
            # Dessiner le texte
            draw.text((x_nom, height + 5), nom_produit, fill='black', font=font)
            draw.text((x_prix, height + 30), prix_text, fill='black', font=font_prix)
            
            # Sauvegarder
            nouvelle_img.save(chemin_image)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du texte: {e}")
    
    @staticmethod
    def imprimer_code_barre(chemin_image):
        """
        Ouvrir l'image pour impression
        """
        try:
            img = Image.open(chemin_image)
            img.show()
            print(f"✅ Image ouverte pour impression: {chemin_image}")
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture de l'image: {e}")
    
    @staticmethod
    def obtenir_chemin_image(code):
        """
        Obtenir le chemin de l'image d'un code-barres
        """
        return os.path.join(IMAGES_DIR, f"{code}.png")
    
    @staticmethod
    def code_barre_existe(code):
        """
        Vérifier si l'image d'un code-barres existe
        """
        chemin = CodeBarre.obtenir_chemin_image(code)
        return os.path.exists(chemin)
