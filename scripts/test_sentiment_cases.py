import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.sentiment.classifier import get_sentiment_classifier

def main():
    print("=== Auditing Sentiment Analysis Model Inputs & Fallbacks ===")
    clf = get_sentiment_classifier()
    print("Classifier Model Name:", clf.model_name)

    cases = [
        ("Positive", "An absolute visual and narrative masterpiece with brilliant acting! 10/10"),
        ("Negative", "Terrible, boring, pretentious trash. Avoid at all costs."),
        ("Mixed", "Visually stunning cinematography, but the pacing was sluggish and the plot faltered."),
        ("Empty", ""),
        ("Whitespace", "    "),
        ("Long Text", "Masterpiece! " * 200)
    ]

    for label, text in cases:
        res = clf.predict_one(text)
        print(f"[{label:<10}] Input len={len(text):<4} -> Label={res['label']:<8} Conf={res['confidence']:.4f} Empty={res['is_empty']}")

if __name__ == "__main__":
    main()
