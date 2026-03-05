"""
Test script to verify OpenRouter integration
"""
import os
from dotenv import load_dotenv
from llm_reader import LLMReader
from llm_interpreter import LLMInterpreter

load_dotenv()

def test_openrouter():
    print("Testing OpenRouter Integration...")
    print(f"API Key present: {bool(os.getenv('OPEN_ROUTER_KEY'))}")
    
    # Test sample medical text
    sample_text = """
    Patient presents with chest pain and shortness of breath.
    History: Hypertension, Type 2 Diabetes.
    Assessment: Acute chest pain, possible angina.
    Plan: EKG, cardiac enzymes, admit for observation.
    """
    
    try:
        # Test Reader
        print("\n1. Testing LLMReader with OpenRouter...")
        reader = LLMReader(provider="openrouter")
        structured = reader.structure_document(sample_text)
        print("✓ Reader successful")
        print(f"Structured output keys: {list(structured.keys())}")
        
        # Test Interpreter
        print("\n2. Testing LLMInterpreter with OpenRouter...")
        interpreter = LLMInterpreter(provider="openrouter")
        clinical_map = interpreter.interpret_meaning(structured)
        print("✓ Interpreter successful")
        print(f"Clinical map keys: {list(clinical_map.keys())}")
        
        print("\n✅ All OpenRouter tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_openrouter()
