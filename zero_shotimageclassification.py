# -*- coding: utf-8 -*-
"""zero-shotimageclassification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1n4tmKm9SlEr-LI3n4Ndk3ewrdreK12FY
"""

from PIL import Image
import requests
import torch
from transformers import CLIPProcessor, CLIPModel
from io import BytesIO

url = "https://upload.wikimedia.org/wikipedia/commons/5/58/MountainLion.jpg"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image.show()  # só para visualização no Colab
else:
    raise Exception(f"Erro ao baixar imagem: {response.status_code}")

# Frases em português para classificação
texts = ["um cachorro", "um gato", "um leão", "um puma", "uma casa", "um carro", "uma floresta"]

# Carregar modelo CLIP
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Preparar entrada
inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)

# Passar pelo modelo
with torch.no_grad():
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image  # similaridade imagem-texto
    probs = logits_per_image.softmax(dim=1)  # converter para probabilidades

# Mostrar resultado
for label, prob in zip(texts, probs[0]):
    print(f"{label}: {prob.item()*100:.2f}%")

# Melhor palpite
best_idx = probs.argmax().item()
print("\n🔍 Melhor descrição segundo o modelo:", texts[best_idx])