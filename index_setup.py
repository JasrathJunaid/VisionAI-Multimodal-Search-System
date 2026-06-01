import os
import shutil
from qdrant_client.models import VectorParams, Distance, PointStruct
from utils import get_all_image_paths, get_image_embedding, get_image_id
from db import client, COLLECTION_NAME
from config import VECTOR_SIZE, MULTIMODAL_FOLDER

def init_collection():
    """Initializes the Qdrant collection if it doesn't exist."""
    if not client:
        print("Cannot initialize collection: Qdrant client is not available.")
        return
        
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created.")
    else:
        print(f"ℹ️ Collection '{COLLECTION_NAME}' already exists.")

def index_images():
    """Indexes all images in the multimodal folder into Qdrant."""
    if not client:
        print("Cannot index images: Qdrant client is not available.")
        return

    image_paths = get_all_image_paths(MULTIMODAL_FOLDER)
    if not image_paths:
        print(f"⚠️ No images found in '{MULTIMODAL_FOLDER}' to index! Please place your 1031 images there.")
        return

    print(f"📸 Found {len(image_paths)} images to process.")

    # Get paths of already indexed points to skip them
    try:
        existing_points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=len(image_paths), with_payload=True)
        existing_paths = {os.path.abspath(p.payload["path"]) for p in existing_points if p.payload and "path" in p.payload}
    except Exception as e:
        print(f"Could not retrieve existing points. Assuming empty collection. Error: {e}")
        existing_paths = set()

    points = []
    for path in image_paths:
        abs_path = os.path.abspath(path)
        if abs_path in existing_paths:
            # print(f"Skipping (already indexed): {path}")
            continue
        
        try:
            print(f"Indexing: {path}")
            emb = get_image_embedding(path)
            if emb:
                img_id = get_image_id(path)
                # Payload stores the original path and the title (filename without extension)
                title = os.path.splitext(os.path.basename(path))[0]
                points.append(PointStruct(id=img_id, vector=emb, payload={"path": path, "title": title}))
        except Exception as e:
            print(f"❌ Failed to index {path}: {e}")

    if points:
        print(f"🚀 Indexing {len(points)} new images...")
        client.upsert(collection_name=COLLECTION_NAME, wait=True, points=points)
        print(f"✅ Indexing complete. Total indexed images: {len(existing_paths) + len(points)}")
    else:
        print("✅ No new images to index.")


if __name__ == '__main__':
    # 1. Initialize the Qdrant collection
    init_collection()
    
    # 2. Index the images (RUN THIS ONLY ONCE!)
    index_images()
