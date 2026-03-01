from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple, List
from core.config import settings

_tokenizer = None
_model = None
_labels = ["positive", "negative", "neutral"]


def _load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        device = "cuda:0" if (settings.use_gpu and torch.cuda.is_available()) else "cpu"
        _tokenizer = AutoTokenizer.from_pretrained(settings.finbert_model)
        _model = AutoModelForSequenceClassification.from_pretrained(
            settings.finbert_model
        ).to(device)
        _model.eval()


def estimate_sentiment(headlines: List[str]) -> Tuple[float, str]:
    if not headlines:
        return 0.0, "neutral"

    _load_model()
    device = next(_model.parameters()).device

    cleaned = [h.strip() for h in headlines if h.strip()]
    if not cleaned:
        return 0.0, "neutral"

    with torch.no_grad():
        tokens = _tokenizer(
            cleaned,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(device)
        logits = _model(
            tokens["input_ids"], attention_mask=tokens["attention_mask"]
        )["logits"]
        aggregated = torch.sum(logits, dim=0)
        probabilities = torch.nn.functional.softmax(aggregated, dim=-1)
        best_idx = torch.argmax(probabilities).item()
        probability = probabilities[best_idx].item()
        sentiment = _labels[best_idx]

    return float(probability), sentiment


def estimate_sentiment_batch(
    headlines: List[str], batch_size: int = 16
) -> List[Tuple[float, str]]:
    if not headlines:
        return []

    _load_model()
    device = next(_model.parameters()).device
    results = []

    for i in range(0, len(headlines), batch_size):
        batch = headlines[i : i + batch_size]
        with torch.no_grad():
            tokens = _tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
            logits = _model(
                tokens["input_ids"], attention_mask=tokens["attention_mask"]
            )["logits"]
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            for probs in probabilities:
                best_idx = torch.argmax(probs).item()
                results.append((probs[best_idx].item(), _labels[best_idx]))

    return results


def get_aggregate_sentiment(headlines: List[str]) -> dict:
    if not headlines:
        return {"sentiment": "neutral", "probability": 0.0, "breakdown": {}}

    per_headline = estimate_sentiment_batch(headlines)
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for _, sentiment in per_headline:
        counts[sentiment] += 1

    total = len(per_headline)
    breakdown = {k: v / total for k, v in counts.items()}

    overall_prob, overall_sentiment = estimate_sentiment(headlines)
    return {
        "sentiment": overall_sentiment,
        "probability": overall_prob,
        "breakdown": breakdown,
        "per_headline": [
            {"headline": h, "sentiment": s, "probability": p}
            for h, (p, s) in zip(headlines, per_headline)
        ],
    }
