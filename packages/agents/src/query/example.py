"""Example usage of Query Agent"""
import logging
from typing import Dict, Any

from .nlp_pipeline import NLPPipeline
from .entity_recognizer import EntityRecognizer
from .intent_classifier import IntentClassifier
from .clarification import ClarificationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_nlp_pipeline():
    """Demonstrate NLP pipeline"""
    print("\n" + "="*60)
    print("NLP Pipeline Demo")
    print("="*60)

    nlp = NLPPipeline()
    
    queries = [
        "What was the shielded transaction volume last week?",
        "Show me price trends over the past month",
        "Are there any anomalies in hash rate today?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        doc = nlp.process(query)
        
        entities = nlp.extract_entities(doc)
        print(f"Entities: {entities}")
        
        structure = nlp.analyze_query_structure(doc)
        print(f"Structure: {structure}")


def demo_entity_recognizer():
    """Demonstrate entity recognizer"""
    print("\n" + "="*60)
    print("Entity Recognizer Demo")
    print("="*60)

    recognizer = EntityRecognizer()
    
    queries = [
        "What was the shielded transaction volume last 7 days?",
        "Show me Zcash price trends from January 1, 2024 to today",
        "Compare transparent vs shielded transactions this month",
        "What caused the 15% price spike yesterday?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        entities = recognizer.recognize_entities(query)
        
        for entity in entities:
            print(f"  - {entity['entity_type']}: {entity['value']} "
                  f"(confidence: {entity['confidence']:.2f})")


def demo_intent_classifier():
    """Demonstrate intent classifier"""
    print("\n" + "="*60)
    print("Intent Classifier Demo")
    print("="*60)

    classifier = IntentClassifier()
    recognizer = EntityRecognizer()
    
    queries = [
        "How has the shielded pool size changed over time?",
        "Are there any unusual spikes in transaction volume?",
        "Compare Zcash price to Bitcoin price",
        "Why did the hash rate drop last week?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        entities = recognizer.recognize_entities(query)
        classification = classifier.classify(query, entities)
        
        print(f"  Intent: {classification['intent_type'].value}")
        print(f"  Confidence: {classification['confidence']:.2f}")
        print(f"  Metrics: {classification['metrics']}")
        if classification['time_range']:
            print(f"  Time Range: {classification['time_range']}")


def demo_clarification():
    """Demonstrate clarification engine"""
    print("\n" + "="*60)
    print("Clarification Engine Demo")
    print("="*60)

    clarification_engine = ClarificationEngine()
    classifier = IntentClassifier()
    recognizer = EntityRecognizer()
    
    # Ambiguous queries
    queries = [
        "Show me the trends",  # Missing metric and time range
        "What happened?",  # Missing everything
        "Compare the values",  # Missing what to compare
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        entities = recognizer.recognize_entities(query)
        intent = classifier.classify(query, entities)
        
        result = clarification_engine.check_for_ambiguity(
            query=query,
            intent=intent,
            entities=entities,
            context={}
        )
        
        if result["clarification_needed"]:
            print("  Clarification needed!")
            print(f"  Reasons: {result['reasons']}")
            for i, question in enumerate(result["questions"], 1):
                print(f"  Question {i}: {question}")
        else:
            print("  No clarification needed")


def demo_full_pipeline():
    """Demonstrate full query processing pipeline"""
    print("\n" + "="*60)
    print("Full Pipeline Demo")
    print("="*60)

    # Initialize components
    nlp = NLPPipeline()
    recognizer = EntityRecognizer()
    classifier = IntentClassifier()
    clarification_engine = ClarificationEngine()
    
    queries = [
        "What was the shielded transaction volume last 7 days?",
        "Show me price trends",  # Ambiguous - missing time range
        "Are there any anomalies in hash rate today?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Processing: {query}")
        print('='*60)
        
        # Step 1: NLP processing
        doc = nlp.process(query)
        print("\n1. NLP Processing:")
        structure = nlp.analyze_query_structure(doc)
        print(f"   Question words: {structure['question_words']}")
        print(f"   Root verb: {structure['root_verb']}")
        
        # Step 2: Entity extraction
        entities = recognizer.recognize_entities(query, doc)
        print("\n2. Entity Extraction:")
        for entity in entities:
            print(f"   - {entity['entity_type']}: {entity['value']}")
        
        # Step 3: Intent classification
        intent = classifier.classify(query, entities)
        print("\n3. Intent Classification:")
        print(f"   Intent: {intent['intent_type'].value}")
        print(f"   Confidence: {intent['confidence']:.2f}")
        print(f"   Metrics: {intent['metrics']}")
        
        # Step 4: Clarification check
        clarification = clarification_engine.check_for_ambiguity(
            query=query,
            intent=intent,
            entities=entities,
            context={}
        )
        print("\n4. Clarification Check:")
        if clarification["clarification_needed"]:
            print("   ⚠️  Clarification needed!")
            for question in clarification["questions"]:
                print(f"   Q: {question}")
        else:
            print("   ✓ Query is clear")


def main():
    """Run all demos"""
    try:
        demo_nlp_pipeline()
        demo_entity_recognizer()
        demo_intent_classifier()
        demo_clarification()
        demo_full_pipeline()
        
        print("\n" + "="*60)
        print("All demos completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error running demos: {e}", exc_info=True)


if __name__ == "__main__":
    main()
