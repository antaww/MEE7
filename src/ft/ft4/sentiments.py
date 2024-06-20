from transformers import pipeline

sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")


def analyze_sentiment(message):
    result = sentiment_analyzer(message)[0]
    if result['label'] == '1 star':
        return {"compound": -1.0}
    elif result['label'] == '2 stars':
        return {"compound": -0.5}
    elif result['label'] == '3 stars':
        return {"compound": 0.0}
    elif result['label'] == '4 stars':
        return {"compound": 0.5}
    elif result['label'] == '5 stars':
        return {"compound": 1.0}
