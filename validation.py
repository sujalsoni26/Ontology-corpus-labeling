"""
validation.py
Validation logic for sentence labeling completeness.
"""

from typing import Dict, List, Tuple, Optional


def validate_label_completeness(
    label_code: str,
    subject_words: List[int],
    object_words: List[int]
) -> Tuple[bool, Optional[str]]:
    """
    Validate if a label assignment is complete based on the label type.
    
    Args:
        label_code: The label code (pdr, pd, pr, p, n)
        subject_words: List of word indices for subject
        object_words: List of word indices for object
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if the label is complete and valid
        - error_message: None if valid, otherwise a helpful error message
    
    Validation Rules:
        - "n" (No alignment): No subject AND no object selected
        - "pdr" (Full alignment): Both subject AND object selected
        - "pd" (Correct Domain): Subject selected AND no object
        - "pr" (Correct Range): Object selected AND no subject
        - "p" (Incorrect D & R): No subject AND no object selected
        - No label assigned: If any words selected, it's incomplete
    """
    has_subject = len(subject_words) > 0
    has_object = len(object_words) > 0
    
    # No label assigned
    if not label_code or label_code == "":
        if has_subject or has_object:
            return False, "⚠️ Please select a label before marking words"
        else:
            return False, "⚠️ Please select a label to complete this sentence"
    
    # Validation rules for each label type
    if label_code == "n":
        # No alignment - should have NO words selected
        if has_subject or has_object:
            return False, "⚠️ No alignment selected - please remove all word selections"
        return True, None
    
    elif label_code == "pdr":
        # Full alignment - must have BOTH subject and object
        if not has_subject and not has_object:
            return False, "⚠️ Full alignment requires both subject and object words"
        elif not has_subject:
            return False, "⚠️ Full alignment requires subject words - please select the subject"
        elif not has_object:
            return False, "⚠️ Full alignment requires object words - please select the object"
        return True, None
    
    elif label_code == "pd":
        # Correct Domain - must have subject, NO object
        if has_object:
            return False, "⚠️ Correct Domain should only have subject words - please remove object selection"
        elif not has_subject:
            return False, "⚠️ Correct Domain requires subject words - please select the subject"
        return True, None
    
    elif label_code == "pr":
        # Correct Range - must have object, NO subject
        if has_subject:
            return False, "⚠️ Correct Range should only have object words - please remove subject selection"
        elif not has_object:
            return False, "⚠️ Correct Range requires object words - please select the object"
        return True, None
    
    elif label_code == "p":
        # Incorrect D & R - should have NO words selected
        if has_subject or has_object:
            return False, "⚠️ Incorrect D&R selected - please remove all word selections"
        return True, None
    
    else:
        # Unknown label code
        return False, f"⚠️ Unknown label code: {label_code}"


def get_label_requirements(label_code: str) -> str:
    """
    Get a human-readable description of what's required for a label type.
    
    Args:
        label_code: The label code (pdr, pd, pr, p, n)
        
    Returns:
        String description of requirements
    """
    requirements = {
        "n": "No words should be selected (no alignment)",
        "pdr": "Both subject and object words must be selected",
        "pd": "Only subject words must be selected",
        "pr": "Only object words must be selected",
        "p": "No words should be selected (incorrect domain and range)",
        "": "Please select a label first"
    }
    
    return requirements.get(label_code, "Unknown label type")


def get_completion_summary(
    label_code: str,
    subject_words: List[int],
    object_words: List[int]
) -> Dict[str, any]:
    """
    Get a summary of the current labeling state.
    
    Args:
        label_code: The label code
        subject_words: List of subject word indices
        object_words: List of object word indices
        
    Returns:
        Dictionary with completion status and details
    """
    is_valid, error_msg = validate_label_completeness(label_code, subject_words, object_words)
    
    return {
        "is_complete": is_valid,
        "error_message": error_msg,
        "label_code": label_code,
        "has_subject": len(subject_words) > 0,
        "has_object": len(object_words) > 0,
        "subject_count": len(subject_words),
        "object_count": len(object_words),
        "requirements": get_label_requirements(label_code)
    }
