import torch
from sentence_transformers import SentenceTransformer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SENTENCE_EMBEDDING_MODEL= SentenceTransformer('all-MiniLM-L6-v2').to(device)