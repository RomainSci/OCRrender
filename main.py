from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import easyocr
from typing import Dict

app = FastAPI()

# CORS configuration - autorise toutes origines
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser le lecteur EasyOCR pour le français
reader = easyocr.Reader(['fr'], gpu=False)  # gpu=True si GPU dispo

def parse_cotisations_easyocr(text_lines) -> Dict:
    """
    Analyse la liste des lignes retournées par EasyOCR
    pour extraire les cotisations annuelles, mensualisées et les totaux.
    
    text_lines = liste de string OCR page par page.
    """
    annuel = {}
    mensuel = {}

    for line in text_lines:
        # Recherche d’une ligne "année ... total €"
        parts = line.replace(',', '.').split()
        if len(parts) >= 2 and parts[0].isdigit():
            try:
                annee = int(parts[0])
                valeur = None
                for part in reversed(parts):
                    if part.replace('.', '').isdigit():
                        valeur = float(part)
                        break
                if valeur is not None:
                    annuel[annee] = valeur
                    mensuel[annee] = round(valeur / 12, 2)
            except Exception:
                continue

    total_annuel = sum(annuel.values())
    total_mensuel = sum(mensuel.values())

    return {
        "cotisationsAnnuel": annuel,
        "cotisationsMensuel": mensuel,
        "totalAnnuel": total_annuel,
        "totalMensuel": total_mensuel,
    }

@app.post("/ocr/extract")
async def extract_cotisations(pdf: UploadFile = File(...)):
    content = await pdf.read()
    images = convert_from_bytes(content)

    all_text_lines = []
    for image in images:
        ocr_result = reader.readtext(image, detail=0)
        all_text_lines.extend(ocr_result)

    parsed = parse_cotisations_easyocr(all_text_lines)
    return parsed
