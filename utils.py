# utils.py

import os
import requests
import tempfile
import traceback
import hashlib
from fpdf import FPDF 
from qdrant_client.models import SearchParams
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from PIL import Image
from sentence_transformers import SentenceTransformer
import wikipedia 
import re 
import json

from config import (
    UNSPLASH_ACCESS_KEY, YOUTUBE_API_KEY,
    VECTOR_SIZE, COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT
) 

MULTIMODAL_FOLDER = "images" 

try:
    model = SentenceTransformer("clip-ViT-B-32")
    def get_text_embedding(text: str): return model.encode(text).tolist()
    def get_image_embedding(image):
        if isinstance(image, str): image = Image.open(image)
        return model.encode(image).tolist()
except Exception as e:
    print(f"Error loading SentenceTransformer/CLIP model: {e}")
    VECTOR_SIZE = 512 
    def get_text_embedding(text: str): return [0.0] * VECTOR_SIZE
    def get_image_embedding(image): return [0.0] * VECTOR_SIZE

try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    client.get_collections() 
except Exception as e:
    print(f"Error connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}: {e}")
    client = None



def online_image_search(query, per_page=10):
    if not UNSPLASH_ACCESS_KEY or "YOUR_UNSPLASH_ACCESS_KEY" in UNSPLASH_ACCESS_KEY:
        print("Unsplash API key not configured. Using mock data.")
        return [{"image": f"https://source.unsplash.com/400x300/?{query},online", "description": "Mock Unsplash Result"}]
        
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}&per_page={per_page}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data=r.json().get("results",[])
        return [{"image":img["urls"]["regular"],"description":img.get("alt_description","")} for img in data]
    except Exception as e:
        print(f"Error fetching Unsplash: {e}")
        return []

def youtube_search(query, max_results=5):
    if not YOUTUBE_API_KEY or "YOUR_YOUTUBE_API_KEY" in YOUTUBE_API_KEY:
        print("YouTube API key not configured. Using mock data.")
        return [{"videoId": "dQw4w9WgXcQ", "title": f"Mock Music for {query}", "thumbnail": "", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ"}]
        
    url=f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&key={YOUTUBE_API_KEY}&maxResults={max_results}"
    try:
        r=requests.get(url).json()
        results=[]
        for item in r.get("items",[]):
            vid=item["id"]["videoId"]
            results.append({
                "videoId":vid,
                "title":item["snippet"]["title"],
                "thumbnail":item["snippet"]["thumbnails"]["medium"]["url"],
                "url":f"https://www.youtube.com/embed/{vid}"
            })
        return results
    except Exception as e:
        print(f"Error fetching YouTube: {e}")
        return []

def search_local_images_by_vector(vector):
    if not client: return []
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=10,
            search_params=SearchParams(exact=False, hnsw_ef=128)
        )
        response=[]
        for r in results:
            rel_path = r.payload["path"].replace("\\","/")
            response.append({"image": f"/local_images/{rel_path}","score": r.score})
        return response
    except Exception as e:
        return []
        
def search_local_images(query):
    try:
        emb = get_text_embedding(query)
        return search_local_images_by_vector(emb)
    except Exception as e:
        return []

def fusion_search(query=None, image_path=None):
    vectors=[]
    if query: vectors.append(get_text_embedding(query))
    if image_path:
        try: vectors.append(get_image_embedding(image_path))
        except Exception as e: return []
    if not vectors: return []
    fusion_vector = [sum(vals)/len(vals) for vals in zip(*vectors)]
    return search_local_images_by_vector(fusion_vector)

def get_wikipedia_content(query):
    """Fetches full Wikipedia content for the explanation. (FIXED)"""
    wiki_data = {"explanation": "", "title": None, "url": None}
    
    try:
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            wiki_data["explanation"] = f"Wikipedia page not found for '{query}'."
            return wiki_data
            
        page_title = search_results[0]
        page = wikipedia.page(page_title, auto_suggest=False, redirect=True)
        
        explanation = page.content
        
        explanation = re.sub(r'={2,}.*?={2,}', '', explanation).strip()
        
        wiki_data["explanation"] = explanation
        wiki_data["title"] = page_title
        wiki_data["url"] = page.url
        
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:5])
        wiki_data["explanation"] = f"Wikipedia requires clarification for '{query}'. Options: {options}."
    except Exception:
        wiki_data["explanation"] = f"Error fetching Wikipedia content for '{query}'. Please check the topic."
        
    return wiki_data

def generate_wiki_based_notes(explanation: str):
    """Generates structured notes by simplifying and bulleting the Wikipedia explanation."""
    
    if not explanation or "Error fetching Wikipedia content" in explanation:
        return "**Notes:** Could not generate study notes as the Wikipedia explanation failed to load."
    notes_content = explanation

    points = [p.strip() for p in notes_content.split('\n\n') if p.strip()]

    markdown_notes = "**Key Concepts:**\n\n"
    
    count = 0
    for point in points:
        clean_point = re.sub(r'={2,}\s*.*?\s*={2,}', '', point).replace('\n', ' ').replace('*', '').replace('-', '').strip()
        
        if len(clean_point) > 50 and count < 7:
             markdown_notes += f"* {clean_point}\n"
             count += 1
    
    if count == 0:
        return "**Notes:** The Wikipedia content was too short or lacked clear sections for automated note generation."

    return markdown_notes


def study_topic_full(query, max_tokens=300):
    result = {"topic": query, "explanation":"", "notes":"", "wikipedia":{}, "images":[], "videos":[], "pdf":""}
    
    print(f"Generating Explanation via Wikipedia for: {query}")
    wiki_data = get_wikipedia_content(query)
    
    result["explanation"] = wiki_data["explanation"]
    if wiki_data["title"]:
         result["wikipedia"] = {
             "title": wiki_data["title"],
             "summary": wiki_data["explanation"][:500] + ("..." if len(wiki_data["explanation"]) > 500 else ""),
             "url": wiki_data["url"]
         }
    else:
        result["wikipedia"] = {"summary": "Error fetching Wikipedia summary or topic is ambiguous."}
        result["explanation"] = f"Error fetching Wikipedia summary or topic is ambiguous for '{query}'."

    print("Generating notes using Wikipedia content (AI APIs removed).")
    result["notes"] = generate_wiki_based_notes(result["explanation"])
        
    result["images"] = [
        {"small": i["image"], "link": i["image"]} 
        for i in online_image_search(query, per_page=6)
    ]
    result["videos"] = youtube_search(query)


    try:
        os.makedirs("multimodal_data", exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(0, 10, f"Study Notes for: {query}\n\n", align='C')
        
        pdf.set_font("Arial", '', 12)
        
        pdf.set_text_color(20, 20, 100) 
        pdf.multi_cell(0, 8, "EXPLANATION (Source: Wikipedia):\n", 0, 'L')
        pdf.set_text_color(0, 0, 0) 
        pdf.multi_cell(0, 6, result["explanation"] + "\n\n")
        pdf.set_text_color(20, 100, 20) 
        pdf.multi_cell(0, 8, "KEY NOTES:", 0, 'L')
        pdf.set_text_color(0, 0, 0) 
        
        clean_notes = result["notes"].replace('**', '').replace('*', '•').replace('-', '•')
        pdf.multi_cell(0, 6, clean_notes + "\n\n")

        temp_dir = tempfile.gettempdir()
        for idx, img in enumerate(result["images"][:3]):
            temp_img_path = os.path.join(temp_dir, f"temp_{os.getpid()}_{idx}.jpg")
            try:
                img_data = requests.get(img["small"], timeout=5).content
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                pdf.image(temp_img_path, w=80) 
            except Exception as e:
                print(f"PDF image embed error: {e}")
            finally:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)

        pdf_filename = f"{query.replace(' ', '_')}_study.pdf"
        pdf_path = os.path.join("multimodal_data", pdf_filename)
        pdf.output(pdf_path)
        result["pdf"] = f"/download_pdf/{pdf_filename}"
        
    except Exception as e:
        print(f"PDF generation failed: {e}")
        traceback.print_exc()
        result["pdf"] = f"PDF generation failed: {str(e)}"

    return result