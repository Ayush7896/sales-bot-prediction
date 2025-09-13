import json

FIlEPATH = "filepath"

def load_config():
    try:
        with open(FIlEPATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] config.json not found!")
        return {}


config = load_config()

def check_quick_faq(user_question):
    """Check if question matches any FAQ keyword"""
    user_question = user_question.lower()
    
    for faq_name, faq_data in config.get("quick_faqs", {}).items():
        keywords = faq_data.get("keywords", [])
        
        # Check if any keyword matches
        for keyword in keywords:
            if keyword in user_question:
                return {
                    "found": True,
                    "answer": faq_data["answer"],
                    "source": faq_data["source"],
                    "category": faq_name
                }
    
    return {"found": False}
