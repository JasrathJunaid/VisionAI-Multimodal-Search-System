# backend.py
"""from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import tempfile
import shutil
# Import all necessary functions from utils.py
from utils import (
    search_local_images, 
    fusion_search as utils_fusion_search, 
    online_image_search, 
    youtube_search as utils_youtube_search, 
    study_topic_full, 
    MULTIMODAL_FOLDER
)

# Folder paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
LOCAL_IMAGES_DIR = os.path.join(BASE_DIR, MULTIMODAL_FOLDER)

# Ensure the directories exist
os.makedirs(LOCAL_IMAGES_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "multimodal_data"), exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=STATIC_DIR)
CORS(app)

# --- Frontend Routes ---
@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/mode/<mode>')
def mode_page(mode):
    if mode == "study":
        return render_template('study.html')
    elif mode == "entertainment":
        return render_template('entertain.html')
    else:
        return "Invalid mode selected", 404

# --- API Routes ---

# 1. Study API (for study.html)
@app.route('/api/study_full')
def study_topic_full(query, max_tokens=300):
    result = {"topic": query, "explanation": "", "notes": "", "images": [], "videos": [], "pdf": ""}

    # 1. Gemini AI (Text Generation)
    if "YOUR_GEMINI_API_KEY" in GEMINI_API_KEY:
        error_msg = "Gemini API key not configured. Using mock data."
        result["explanation"] = error_msg
        result["notes"] = f"{error_msg}\n\nThis is a mock note for {query}."
    else:
        try:
            # ✅ Gemini 1.5 / 2.5 API structure
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"Explain clearly and give structured study notes for: {query}. "
                                        f"Keep the explanation clear, simple, and short for students. "
                                        f"Then give bullet points for key notes."
                            }
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens}
            }

            r = requests.post(f"{url}?key={GEMINI_API_KEY}", json=payload, headers=headers, timeout=20)
            print("Gemini response:", r.text)  # 🧩 Debug log
            r.raise_for_status()
            data = r.json()

            # ✅ Robust text extraction (covers all Gemini formats)
            text = ""
            if "candidates" in data:
                cand = data["candidates"][0]
                if "content" in cand and isinstance(cand["content"], dict):
                    text = cand["content"].get("parts", [{}])[0].get("text", "")
                elif "content" in cand and isinstance(cand["content"], list):
                    text = cand["content"][0].get("parts", [{}])[0].get("text", "")
                elif "output_text" in cand:
                    text = cand["output_text"]

            if not text.strip():
                text = "⚠️ Gemini returned no text. Try again or check the API quota."

            result["explanation"] = text
            result["notes"] = text

        except requests.exceptions.RequestException as e:
            print("Gemini API Request Error:", e.response.text if e.response else str(e))
            result["explanation"] = f"Gemini API request error: {e}"
            result["notes"] = result["explanation"]
        except Exception as e:
         import traceback
         print("🔥 Study API error:", str(e))
         traceback.print_exc()
 

    # 2. Online images & videos
    result["images"] = [
        {"small": i["image"], "link": i["image"]}
        for i in online_image_search(query, per_page=6)
    ]
    result["videos"] = [
        {"videoId": v["videoId"], "title": v["title"], "thumbnail": v["thumbnail"], "url": v["url"]}
        for v in youtube_search(query)
    ]

    # 3. PDF generation
    try:
        os.makedirs("multimodal_data", exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(0, 10, f"Study Notes for: {query}\n\n")
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, result["notes"] + "\n\n")

        temp_dir = tempfile.gettempdir()
        for idx, img in enumerate(result["images"]):
            temp_img_path = os.path.join(temp_dir, f"temp_{os.getpid()}_{idx}.jpg")
            try:
                img_data = requests.get(img["small"], timeout=5).content
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                pdf.image(temp_img_path, w=80)
            except Exception as e:
                print(f"PDF image error: {e}")
            finally:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)

        pdf_path = os.path.join("multimodal_data", f"{query.replace(' ', '_')}_study.pdf")
        pdf.output(pdf_path)
        result["pdf"] = pdf_path
    except Exception as e:
        result["pdf"] = f"PDF generation failed: {str(e)}"

    return result



# 2. Text Search (Local Index)
@app.route('/search_text')
def search_text_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        # returns [{'image': '/local_images/path/to/img.jpg', 'score': 0.8}]
        return jsonify(search_local_images(q))
    except Exception as e:
        print(f"Text search error: {e}")
        return jsonify([])

# 3. Fusion Search (Text + Image - Local Index) (CRITICAL FIX)
@app.route('/search_fusion', methods=['POST'])
def search_fusion_route():
    q = request.form.get('query', '')
    uploaded_file = request.files.get('image') # Frontend sends file with key 'image'

    if not q and not uploaded_file: return jsonify([])

    temp_file_path = None
    try:
        if uploaded_file:
            # Save file temporarily on the server
            temp_dir = tempfile.gettempdir()
            temp_file_name = f"upload_{os.getpid()}_{uploaded_file.filename}"
            temp_file_path = os.path.join(temp_dir, temp_file_name)
            uploaded_file.save(temp_file_path)

        results = utils_fusion_search(query=q, image_path=temp_file_path)
        return jsonify(results)
    except Exception as e:
        print(f"Fusion search error: {e}")
        return jsonify([])
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# 4. Online Image Search (Unsplash)
@app.route('/search_online')
def search_online_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        # returns [{'image': 'http://unsplash.com/url...', 'description': '...'}]
        return jsonify(online_image_search(q))
    except Exception as e:
        print(f"Online search error: {e}")
        return jsonify([])


# 5. YouTube Music Search
@app.route('/search_music')
def search_music_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        # returns [{'url': 'https://embed...', 'title': '...'}, ...]
        results = utils_youtube_search(q)
        response = [{"url": r["url"], "title": r["title"]} for r in results]
        return jsonify(response)
    except Exception as e:
        print(f"Music search error: {e}")
        return jsonify([])


# --- Static/Download Routes ---

# Route to serve local indexed images (images/ folder)
@app.route('/local_images/<path:filename>')
def serve_local_images(filename):
    return send_from_directory(LOCAL_IMAGES_DIR, filename)

# Route to download the generated PDF (multimodal_data/ folder)
@app.route('/download_pdf/<filename>')
def download_pdf_file(filename):
    pdf_dir = os.path.join(BASE_DIR, "multimodal_data")
    full_path = os.path.join(pdf_dir, filename)
    if os.path.exists(full_path):
        return send_file(full_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    return "PDF not found", 404

if __name__ == '__main__':
    # Initial Indexing (Uncomment this line to run indexing when the server starts)
    # from utils import index_local_images
    # index_local_images()
    app.run(debug=True) 
    backend.py

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import tempfile
import traceback 

from config import (
    UNSPLASH_ACCESS_KEY, 
    YOUTUBE_API_KEY, 
) 

from utils import (
    search_local_images, 
    fusion_search, 
    online_image_search, 
    youtube_search, 
    study_topic_full, 
    MULTIMODAL_FOLDER
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
LOCAL_IMAGES_DIR = os.path.join(BASE_DIR, MULTIMODAL_FOLDER)
PDF_DOWNLOAD_DIR = os.path.join(BASE_DIR, "multimodal_data")

os.makedirs(LOCAL_IMAGES_DIR, exist_ok=True)
os.makedirs(PDF_DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=STATIC_DIR)
CORS(app)

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/mode/<mode>')
def mode_page(mode):
    if mode == "study":
        return render_template('study.html')
    elif mode == "entertainment":
        return render_template('entertain.html')
    else:
        return "Invalid mode selected", 404


@app.route('/api/study_full')
def study_full_route(): 
    q = request.args.get('q', request.args.get('query', '')) 
    max_tokens = int(request.args.get('max_tokens', 300)) 
    if not q:
        return jsonify({"error": "Query parameter 'q' is missing."}), 400
    
    try:
        data = study_topic_full(query=q, max_tokens=max_tokens)
        return jsonify(data)
    except Exception as e:
        print(" Study API error:", str(e))
        traceback.print_exc()
        return jsonify({"error": f"Internal server error while processing study request: {str(e)}"}), 500


@app.route('/search_text')
def search_text_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        return jsonify(search_local_images(q))
    except Exception as e:
        print(f"Text search error: {e}")
        traceback.print_exc()
        return jsonify([])

@app.route('/search_fusion', methods=['POST'])
def search_fusion_route():
    q = request.form.get('query', '')
    uploaded_file = request.files.get('image')

    if not q and not uploaded_file: return jsonify([])

    temp_file_path = None
    try:
        if uploaded_file:
            temp_dir = tempfile.gettempdir()
            temp_file_name = f"upload_{os.getpid()}_{uploaded_file.filename}"
            temp_file_path = os.path.join(temp_dir, temp_file_name)
            uploaded_file.save(temp_file_path)

        results = fusion_search(query=q, image_path=temp_file_path)
        return jsonify(results)
    except Exception as e:
        print(f"Fusion search error: {e}")
        traceback.print_exc()
        return jsonify([])
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.route('/search_online')
def search_online_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        return jsonify(online_image_search(q))
    except Exception as e:
        print(f"Online search error: {e}")
        traceback.print_exc()
        return jsonify([])


@app.route('/search_music')
def search_music_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        results = youtube_search(q)
        response = [{"url": r["url"], "title": r["title"]} for r in results]
        return jsonify(response)
    except Exception as e:
        print(f"Music search error: {e}")
        traceback.print_exc()
        return jsonify([])



@app.route('/local_images/<path:filename>')
def serve_local_images(filename):
    return send_from_directory(LOCAL_IMAGES_DIR, filename)

@app.route('/download_pdf/<filename>')
def download_pdf_file(filename):
    full_path = os.path.join(PDF_DOWNLOAD_DIR, filename)
    if os.path.exists(full_path):
        return send_file(full_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    return "PDF not found", 404

if __name__ == '__main__':
    app.run(debug=True)"""


# backend.py
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import tempfile
import traceback 
from fpdf import FPDF  # Required for generating the PDF on the fly

from config import (
    UNSPLASH_ACCESS_KEY, 
    YOUTUBE_API_KEY, 
) 

from utils import (
    search_local_images, 
    fusion_search, 
    online_image_search, 
    youtube_search, 
    study_topic_full, 
    MULTIMODAL_FOLDER
)

# --- DIRECTORY CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
LOCAL_IMAGES_DIR = os.path.join(BASE_DIR, MULTIMODAL_FOLDER)
PDF_DOWNLOAD_DIR = os.path.join(BASE_DIR, "multimodal_data")

os.makedirs(LOCAL_IMAGES_DIR, exist_ok=True)
os.makedirs(PDF_DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=STATIC_DIR)
CORS(app)

# --- PDF GENERATION HELPER FUNCTION ---
def generate_pdf_file(topic, content):
    """Creates a PDF in a temporary location and returns the path."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Study Guide: {topic}", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=12)
    # FPDF default fonts only support Latin-1. We clean the text to avoid crashes.
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    
    # Save to a temporary file that won't be deleted until we serve it
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf.output(temp_file.name)
    return temp_file.name

# --- MAIN ROUTES ---

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/mode/<mode>')
def mode_page(mode):
    if mode == "study":
        return render_template('study.html')
    elif mode == "entertainment":
        return render_template('entertain.html')
    else:
        return "Invalid mode selected", 404

@app.route('/api/study_full')
def study_full_route(): 
    q = request.args.get('q', request.args.get('query', '')) 
    max_tokens = int(request.args.get('max_tokens', 300)) 
    if not q:
        return jsonify({"error": "Query parameter 'q' is missing."}), 400
    
    try:
        data = study_topic_full(query=q, max_tokens=max_tokens)
        # Ensure 'topic' is in the response so JS can use it for the PDF name
        data['topic'] = q 
        return jsonify(data)
    except Exception as e:
        print(" Study API error:", str(e))
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# --- THE DOWNLOAD ROUTE (Matches your JS pdfUrl) ---
@app.route('/download_study_guide')
def download_study_guide():
    topic = request.args.get('topic', 'Study_Notes')
    notes = request.args.get('notes', 'No content available.')
    
    try:
        # 1. Generate the PDF file on the fly
        file_path = generate_pdf_file(topic, notes)
        
        # 2. Send the file to the browser
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{topic.replace(' ', '_')}_StudyGuide.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Download Route Error: {e}")
        return "Error: Could not generate PDF.", 500

# --- ADDITIONAL SEARCH ROUTES ---

@app.route('/search_text')
def search_text_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        return jsonify(search_local_images(q))
    except Exception as e:
        print(f"Text search error: {e}")
        return jsonify([])

@app.route('/search_fusion', methods=['POST'])
def search_fusion_route():
    q = request.form.get('query', '')
    uploaded_file = request.files.get('image')
    if not q and not uploaded_file: return jsonify([])

    temp_file_path = None
    try:
        if uploaded_file:
            temp_dir = tempfile.gettempdir()
            temp_file_name = f"upload_{os.getpid()}_{uploaded_file.filename}"
            temp_file_path = os.path.join(temp_dir, temp_file_name)
            uploaded_file.save(temp_file_path)

        results = fusion_search(query=q, image_path=temp_file_path)
        return jsonify(results)
    except Exception as e:
        print(f"Fusion search error: {e}")
        return jsonify([])
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route('/search_online')
def search_online_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        return jsonify(online_image_search(q))
    except Exception as e:
        print(f"Online search error: {e}")
        return jsonify([])

@app.route('/search_music')
def search_music_route():
    q = request.args.get('query', '')
    if not q: return jsonify([])
    try:
        results = youtube_search(q)
        response = [{"url": r["url"], "title": r["title"]} for r in results]
        return jsonify(response)
    except Exception as e:
        print(f"Music search error: {e}")
        return jsonify([])

@app.route('/local_images/<path:filename>')
def serve_local_images(filename):
    return send_from_directory(LOCAL_IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)
