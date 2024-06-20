import spacy

nlp = spacy.load("fr_core_news_sm")


def extract_keywords(message):
    doc = nlp(message)
    entities = [ent.text for ent in doc.ents]
    keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]

    return {
        "entities": entities,
        "keywords": keywords,
        "sentences": [sent.text for sent in doc.sents]
    }
