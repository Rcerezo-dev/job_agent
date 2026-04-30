# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR.parent / ".env")

KEYWORDS = [
    "ai engineer junior",
    "machine learning engineer junior",
    "llm engineer",
    "nlp engineer junior",
    "mlops junior",
    "python developer ai",
    "data scientist junior",
    "generative ai developer",
]

LOCATION = "Madrid"

CSV_FILE = BASE_DIR / "jobs.csv"
USER_NAME  = os.getenv("USER_NAME",  "Your Name")
USER_EMAIL = os.getenv("USER_EMAIL", "")
USER_PHONE = os.getenv("USER_PHONE", "")
USER_CITY  = os.getenv("USER_CITY",  "")
LINKEDIN   = os.getenv("LINKEDIN",   "")
GITHUB_URL = os.getenv("GITHUB_URL", "")

SKILLS = [
    # ML / Deep Learning
    "Python",
    "TensorFlow",
    "Keras",
    "PyTorch",
    "scikit-learn",
    "Pandas",
    # LLM / GenAI
    "LangChain",
    "LangGraph",
    "HuggingFace Transformers",
    "LoRA / QLoRA",
    "RAG",
    # MLOps & deployment
    "MLflow",
    "FastAPI",
    "Docker",
    "Terraform",
    # Cloud & tools
    "Amazon Bedrock",
    "ChromaDB",
    "Langfuse",
    "RAGAS",
    "spaCy",
    # Soft skills
    "Communication",
    "English C1",
    "Education Technology",
]

EXPERIENCE = [
    {
        "role": "AI Engineering",
        "company": "KeepCoding Bootcamp",
        "period": "2025 – 2026",
        "bullets": [
            "NormaBot — ReAct agent for EU AI regulation compliance: RAG with ChromaDB, Amazon Bedrock, XGBoost + SHAP, LangGraph, Streamlit, Docker and Terraform",
            "Fine-tuning Mistral 7B with LoRA/QLoRA to generate B1 English teaching materials for vocational students",
            "Multimodal classifier of 7 dermatological lesion types combining image and clinical data with TensorFlow and MobileNetV3 — 78.4% accuracy",
            "LangGraph + GPT-4 pipeline to batch-evaluate student essays with individual error analysis reports",
            "Full MLOps pipeline: NLP model with MLflow for experiment tracking and deployment via FastAPI",
            "NLP benchmarking: classical methods vs. DistilBERT on 5k Amazon reviews — 0.80 accuracy",
            "Regression model for Airbnb price prediction in Madrid with rigorous methodology and no data leakage",
        ],
    },
    {
        "role": "English, Language and Science Teacher",
        "company": "González Cañadas",
        "period": "2019 – Present",
        "bullets": [
            "Training teachers in digital tools and active methodologies",
            "Erasmus Coordinator and OTE Manager (Oxford Test of English)",
            "Teaching experience that originated two AI projects: automatic essay evaluation system and fine-tuned LLM for English exercise generation",
        ],
    },
    {
        "role": "English, Language and Science Teacher",
        "company": "IES Juan Ramón Jiménez · Casablanca",
        "period": "2018",
        "bullets": [],
    },
]

EDUCATION = [
    {
        "degree": "Bootcamp en Inteligencia Artificial · Full Stack AI",
        "institution": "KeepCoding®",
        "period": "2025 – 2026",
        "bullets": [
            "Proyecto final: NormaBot — agente ReAct de cumplimiento normativo con RAG (ChromaDB), "
            "XGBoost + SHAP, LangGraph, Docker y Terraform",
        ],
    },
    {
        "degree": "Máster en Profesor de Educación Secundaria, Bachillerato e Idiomas",
        "institution": "Universidad de Salamanca",
        "period": "2016 – 2017",
        "bullets": [],
    },
    {
        "degree": "Grado en Estudios Ingleses",
        "institution": "Universidad de Salamanca",
        "period": "2010 – 2014",
        "bullets": [
            "Erasmus year at University of Leicester (2012–2013)",
        ],
    },
]

LANGUAGES = [
    {"language": "Spanish", "level": "Native"},
    {"language": "English", "level": "C1 — OTE certified"},
]

GITHUB_PROJECTS = [
    {
        "name": "NormaBot",
        "description": "ReAct agent for EU AI Act compliance: RAG with ChromaDB, Amazon Bedrock, XGBoost + SHAP, LangGraph, Streamlit, Docker and Terraform",
        "tech": ["LangGraph", "RAG", "ChromaDB", "Amazon Bedrock", "Docker", "Terraform"],
        "url": "",  # add your GitHub URL
    },
    {
        "name": "English Teacher LLM",
        "description": "Fine-tuning Mistral 7B with LoRA/QLoRA to generate B1 English teaching materials for vocational students",
        "tech": ["Mistral 7B", "LoRA", "QLoRA", "HuggingFace Transformers"],
        "url": "",
    },
    {
        "name": "DermClassifier",
        "description": "Multimodal classifier of 7 dermatological lesion types combining image and clinical data — TensorFlow + MobileNetV3, 78.4% accuracy",
        "tech": ["TensorFlow", "Keras", "MobileNetV3", "Multimodal ML"],
        "url": "",
    },
    {
        "name": "Essay Evaluator Pipeline",
        "description": "LangGraph + GPT-4 pipeline to batch-evaluate student essays with individual error analysis reports",
        "tech": ["LangGraph", "GPT-4", "LangChain", "Python"],
        "url": "",
    },
    {
        "name": "MLOps Pipeline",
        "description": "End-to-end MLOps pipeline: NLP model with MLflow experiment tracking and deployment via FastAPI",
        "tech": ["MLflow", "FastAPI", "Docker", "NLP", "Python"],
        "url": "",
    },
    {
        "name": "NLP Benchmarking",
        "description": "Classical NLP methods vs. DistilBERT on 5k Amazon reviews — 0.80 accuracy",
        "tech": ["DistilBERT", "HuggingFace Transformers", "scikit-learn"],
        "url": "",
    },
    {
        "name": "Airbnb Price Predictor",
        "description": "Regression model for Airbnb price prediction in Madrid with rigorous methodology and no data leakage",
        "tech": ["scikit-learn", "Pandas", "Regression", "Python"],
        "url": "",
    },
]