from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import pytesseract
import re
from typing import Dict

app = FastAPI()

# Configuration CORS - autorise toutes les origines
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # changer pour domaine du frontend en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_cotisations_table(text: str) -> Dict:
    """
    Analyse le texte OCR pour extraire les cotisations annuelles, mensualisées et les totaux.
    """
    pattern = re.compile(
        r"^\s*(\d+)\s+[\d.,\s]+€\s+[\d.,\s]+€\s+([\d.,\s]+)\s*€", 
        re.MULTILINE
    )
    annuel = {}
    mensuel = {}
    for match in pattern.finditer(text):
        annee = int(match.group(1))
        total_annuel = float(match.group(2).replace(' ', '').replace(',', '.'))
        annuel[annee] = total_annuel
        mensuel[annee] = round(total_annuel / 12, 2)
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
    # Lecture du fichier PDF envoyé
    content = await pdf.read()
    # Conversion PDF en images
    pages = convert_from_bytes(content)
    full_text = ''
    # OCR sur chaque page/image
    for page in pages:
        text = pytesseract.image_to_string(page, lang="fra")
        full_text += text + "\n"
    # Extraction métier depuis le texte OCR
    result = parse_cotisations_table(full_text)
    return result

