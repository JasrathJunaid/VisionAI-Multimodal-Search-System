import os
from qdrant_client.models import VectorParams, Distance, PointStruct
from db import client, COLLECTION_NAME
from embedding import get_image_embedding

def get_all_image_paths(dataset_folder="images"):
    paths = []
    for root, _, files in os.walk(dataset_folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                paths.append(os.path.join(root, f))
    return paths

def init_collection(vector_size=512):
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created.")
    else:
        print(f"ℹ️ Collection '{COLLECTION_NAME}' exists.")

def index_dataset(dataset_folder="images"):
    init_collection()
    paths = get_all_image_paths(dataset_folder)
    points = []
    for idx, path in enumerate(paths):
        emb = get_image_embedding(path)
        points.append(PointStruct(
            id=idx,
            vector=emb,
            payload={"path": path, "title": f"{os.path.basename(os.path.dirname(path))} image {idx}"}
        ))
        if len(points) >= 100:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            points = []
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ Indexed {len(paths)} images.")

if __name__ == "__main__":
    index_dataset()
