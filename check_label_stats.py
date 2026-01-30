"""
Quick script to print how many sentences are labeled by any user.
Run: python check_label_stats.py
"""
from database import get_labeled_sentence_stats

total, labeled = get_labeled_sentence_stats()
unlabeled = total - labeled
print(f"Total sentences in DB: {total}")
print(f"Sentences labeled by at least one user: {labeled}")
print(f"Unlabeled sentences: {unlabeled}")
if total > 0:
    print(f"In 'Unlabeled only' mode you will see {unlabeled} sentence(s).")
