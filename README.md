# VisionAI – Multimodal Search System

## Overview

VisionAI is a multimodal AI search system designed to retrieve and explore visual and textual content using semantic similarity. The system uses CLIP-based embeddings to represent content in a shared vector space and Qdrant for vector storage, indexing, and similarity-based retrieval.

The project includes a Python-based backend, embedding generation pipeline, Qdrant database integration, search interface, Study mode, and Entertainment mode.

## Key Features

* Semantic search using multimodal embeddings
* Text-to-image search
* Image-based similarity search
* Vector storage and retrieval using Qdrant
* CLIP-based embedding generation
* Interactive search interface
* Study mode for learning-oriented content exploration
* Entertainment mode for multimedia content exploration
* Python-based backend and processing pipeline

## Technology Stack

* Python
* CLIP
* Qdrant Vector Database
* PyTorch
* Transformers
* Flask
* HTML
* CSS
* JavaScript

---

## Project Structure

```text
VisionAI-Multimodal-Search-System/
│
├── backend.py          # Backend application
├── db.py               # Database operations
├── embedding.py        # Embedding generation
├── download_images.py  # Image acquisition/preparation
├── index_setup.py      # Search index configuration
├── init_qdrant.py      # Qdrant collection initialization
├── search_ui.py        # Search interface
├── utils.py            # Utility functions
│
├── welcome.html        # Main/welcome interface
├── study.html          # Study mode interface
├── entertain.html      # Entertainment interface
├── style.css           # Frontend styling
│
└── README.md
```

---

# How to Run

## 1. Clone the Repository

```bash
git clone https://github.com/JasrathJunaid/VisionAI-Multimodal-Search-System.git
cd VisionAI-Multimodal-Search-System
```

## 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

> If `requirements.txt` is not included in the repository, create one containing the packages required by the project before running this step.

## 4. Configure Qdrant

Make sure Qdrant is running locally or configure the project to connect to your Qdrant instance.

Example local Qdrant configuration:

```text
Host: localhost
Port: 6333
```

Start Qdrant according to your local installation method.

## 5. Initialize the Vector Database

Run the Qdrant initialization script:

```bash
python init_qdrant.py
```

This creates/configures the required vector collection for the application.

## 6. Generate Embeddings / Prepare the Index

Run the embedding and indexing scripts as required:

```bash
python embedding.py
python index_setup.py
```

These components prepare the content and create the vector representations used for semantic search.

## 7. Start the Application

Run the backend:

```bash
python backend.py
```

If the search interface is launched separately, run:

```bash
python search_ui.py
```

Then open the local address displayed in the terminal, for example:

```text
http://127.0.0.1:5000
```

---

# Usage

After starting the application, users can interact with the available interfaces to:

1. Enter a search query.
2. Retrieve semantically similar content.
3. Explore image-based search results.
4. Use the Study interface for learning-oriented content.
5. Explore the Entertainment interface for multimedia content.

---

# Important Setup Notes

* Ensure the required Python version is installed.
* Install all dependencies before running the application.
* Qdrant must be running before performing vector search operations.
* Configure required paths, model locations, and database settings according to your local environment.
* Large datasets and AI models may require additional storage and computational resources.

## Future Improvements

* Improve retrieval accuracy through better multimodal indexing.
* Add additional content modalities.
* Improve ranking and filtering of search results.
* Enhance the user interface and deployment workflow.
* Add more advanced multimodal query capabilities.
