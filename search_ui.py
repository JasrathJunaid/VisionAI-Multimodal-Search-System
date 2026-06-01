from embedding import get_image_embedding, get_text_embedding
from utils import qdrant_search, search_unsplash, path_to_url



UNSPLASH_KEY = ""  # Your Unsplash key

def search_image(image_input, top_k=5):
    try:
        emb = get_image_embedding(image_input)
        results = qdrant_search(emb, top_k)
        if not results:
            results = search_unsplash("image", top_k, UNSPLASH_KEY)
        return [path_to_url(r.payload.get("path")) if "D:" in r.payload.get("path","") else r.payload.get("path") for r in results]
    except:
        return []

def search_text(text, top_k=5):
    try:
        emb = get_text_embedding(text)
        results = qdrant_search(emb, top_k)
        if not results:
            results = search_unsplash(text, top_k, UNSPLASH_KEY)
        return [path_to_url(r.payload.get("path")) if "D:" in r.payload.get("path","") else r.payload.get("path") for r in results]
    except:
        return []

def fusion_search(text, image_input, alpha=0.5, top_k=5):
    try:
        img_vec = get_image_embedding(image_input)
        txt_vec = get_text_embedding(text)
        fusion_vec = [(alpha*i + (1-alpha)*t) for i,t in zip(img_vec, txt_vec)]
        results = qdrant_search(fusion_vec, top_k)
        if not results:
            results = search_unsplash(text, top_k, UNSPLASH_KEY)
        return [path_to_url(r.payload.get("path")) if "D:" in r.payload.get("path","") else r.payload.get("path") for r in results]
    except:
        return []
