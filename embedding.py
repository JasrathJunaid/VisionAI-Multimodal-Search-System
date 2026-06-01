from sentence_transformers import SentenceTransformer
from PIL import Image
import torch

model = SentenceTransformer("clip-ViT-B-32")

def get_image_embedding(image_path):
    img = Image.open(image_path).convert("RGB")
    emb = model.encode(img, convert_to_numpy=True)
    return emb.tolist()

def get_text_embedding(text):
    return model.encode(text, convert_to_numpy=True).tolist()
