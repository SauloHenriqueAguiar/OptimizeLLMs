# -*- coding: utf-8 -*-
"""Analise Robustez Visao Computacional.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1iEDqVBkb5LMupcYXW3HR63dQkU4e2YbN
"""

!pip install transformers torchvision

import torch
from torchvision import transforms
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from transformers import CLIPProcessor, CLIPModel
import numpy as np

# 🔁 Baixar imagem de exemplo
img_url = "https://raw.githubusercontent.com/pytorch/hub/master/images/dog.jpg"  # imagem confiável
response = requests.get(img_url)
image = Image.open(BytesIO(response.content)).convert("RGB")

# Mostrar imagem original
plt.imshow(image)
plt.title("Original Image")
plt.axis("off")
plt.show()

# 🧠 Carregar modelo CLIP
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 🏷️ Rótulos candidatos (zero-shot)
labels = ["a photo of a dog", "a photo of a cat", "a photo of a lion", "a photo of a bird"]

# 🔍 Classificação da imagem original
inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)
probs = outputs.logits_per_image.softmax(dim=1).detach().numpy()[0]

# Mostrar resultados
for label, prob in zip(labels, probs):
    print(f"{label}: {prob:.4f}")

"""# adição de ruídos"""

def add_gaussian_noise(img, mean=0, std=150):
    img_np = np.array(img).astype(np.float32)
    noise = np.random.normal(mean, std, img_np.shape)
    noisy_img_np = np.clip(img_np + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_img_np)

noisy_image = add_gaussian_noise(image)

# Mostrar imagem com ruído muito forte
plt.imshow(noisy_image)
plt.title("Noisy Image (Very Strong)")
plt.axis("off")
plt.show()

# 🔍 Classificação da imagem com ruído
inputs_noisy = processor(text=labels, images=noisy_image, return_tensors="pt", padding=True)
outputs_noisy = model(**inputs_noisy)
probs_noisy = outputs_noisy.logits_per_image.softmax(dim=1).detach().numpy()[0]

print("\n🔎 Probabilidades após ruído:")
for label, prob in zip(labels, probs_noisy):
    print(f"{label}: {prob:.4f}")

"""ataques adversariais"""

!pip install torch torchvision torchattacks --quiet

import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import torchattacks

# Função para mostrar imagem
def imshow(img, title=None):
    img = img.permute(1, 2, 0).numpy()
    plt.imshow(img)
    if title:
        plt.title(title)
    plt.axis('off')
    plt.show()

# Transformações para o modelo
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Carregar modelo pré-treinado
model = models.resnet50(pretrained=True)
model.eval()

# Carregar imagem (usando a original ou com ruído leve)
img_tensor = transform(image).unsqueeze(0)  # [1, 3, 224, 224]

import torchvision.datasets as datasets

# Baixar os nomes das classes do ImageNet
LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
import urllib
labels = urllib.request.urlopen(LABELS_URL).read().decode("utf-8").splitlines()

# Predição original
with torch.no_grad():
    output = model(img_tensor)
    _, predicted = output.max(1)
    print(f"✅ Classe predita (antes do ataque): {labels[predicted]}")

imshow(img_tensor.squeeze(), f"Original: {labels[predicted]}")

from torchattacks import FGSM

# FGSM (Fast Gradient Sign Method)
attack = FGSM(model, eps=0.05)  # Eps define a intensidade do ataque
adv_img = attack(img_tensor, torch.tensor([predicted]))

# Nova predição com imagem adversarial
with torch.no_grad():
    output_adv = model(adv_img)
    _, adv_pred = output_adv.max(1)
    print(f"🚨 Classe predita (após ataque): {labels[adv_pred]}")

imshow(adv_img.squeeze(), f"Adversarial: {labels[adv_pred]}")

from torchattacks import PGD, DeepFool

# Imagem original deve estar com requires_grad=True para DeepFool
img_tensor.requires_grad = True

def apply_attack(attack, img, label_idx, attack_name):
    adv_img = attack(img, torch.tensor([label_idx]))

    with torch.no_grad():
        output = model(adv_img)
        _, adv_pred = output.max(1)

    imshow(adv_img.squeeze(), f"{attack_name}: {labels[adv_pred]}")
    print(f"{attack_name} predição: {labels[adv_pred]}")

    return adv_img

# Ataque PGD (mais forte que FGSM)
pgd = PGD(model, eps=0.05, alpha=0.01, steps=40)
adv_pgd = apply_attack(pgd, img_tensor, predicted.item(), "PGD")

"""Mudança de domínio (domain shift)"""

import numpy as np
import torch
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
from torchvision import transforms
import requests

# Carregar a imagem original
img_url = "https://raw.githubusercontent.com/pytorch/hub/master/images/dog.jpg"  # imagem confiável"
response = requests.get(img_url, stream=True)
image = Image.open(response.raw).convert("RGB")

# Exibir imagem original
plt.imshow(image)
plt.title("Imagem Original")
plt.axis("off")
plt.show()

# Função para aplicar o Domain Shift
def apply_domain_shift(image):
    # 1. Alteração de brilho
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.5)  # Aumentar o brilho (valores > 1)

    # 2. Alteração de contraste
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # Aumentar o contraste (valores > 1)

    # 3. Alteração de saturação
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(0.5)  # Reduzir a saturação (valores < 1)

    # 4. Adicionar ruído (simulando mudanças no domínio)
    noise = np.random.normal(0, 25, (image.size[1], image.size[0], 3)).astype(np.uint8)  # Ruído
    noisy_image = np.array(image) + noise
    noisy_image = np.clip(noisy_image, 0, 255)  # Garantir que os valores sejam válidos
    image = Image.fromarray(noisy_image.astype(np.uint8))

    return image

# Aplicar mudança de domínio
domain_shifted_image = apply_domain_shift(image)

# Exibir imagem com mudança de domínio
plt.imshow(domain_shifted_image)
plt.title("Imagem com Mudança de Domínio")
plt.axis("off")
plt.show()

# Transformar para tensor para predição
transform = transforms.ToTensor()

# Definir o dispositivo (GPU ou CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Transferir para o dispositivo
img_tensor_shifted = transform(domain_shifted_image).unsqueeze(0).to(device)

# Predição com a imagem alterada (após o Domain Shift)
with torch.no_grad():
    output = model(img_tensor_shifted)
    _, predicted = output.max(1)
    print(f"Predição após Mudança de Domínio: {labels[predicted]}")