from keybert import KeyBERT

model = KeyBERT()

def extract_keywords(text: str, num_keywords: int = 5):
    extracted = model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=num_keywords)
    return " ".join([keyword for keyword, _ in extracted])