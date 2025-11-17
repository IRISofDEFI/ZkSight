"""Natural Language Processing pipeline for query parsing"""
import logging
from typing import Dict, List, Any, Optional
import spacy
from spacy.language import Language
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class NLPPipeline:
    """
    NLP pipeline for processing natural language queries.
    
    Uses spaCy for entity extraction and linguistic analysis.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NLP pipeline.

        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
        """
        self.model_name = model_name
        self.nlp: Optional[Language] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load spaCy model"""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(
                f"Model {self.model_name} not found. "
                f"Downloading..."
            )
            import subprocess
            subprocess.run(
                ["python", "-m", "spacy", "download", self.model_name],
                check=True
            )
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Downloaded and loaded spaCy model: {self.model_name}")

    def process(self, text: str) -> Doc:
        """
        Process text through NLP pipeline.

        Args:
            text: Input text to process

        Returns:
            spaCy Doc object with linguistic annotations
        """
        if self.nlp is None:
            raise RuntimeError("NLP model not loaded")
        
        doc = self.nlp(text)
        return doc

    def extract_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """
        Extract named entities from processed document.

        Args:
            doc: spaCy Doc object

        Returns:
            List of entity dictionaries with type, text, and position
        """
        entities = []
        for ent in doc.ents:
            entities.append({
                "type": ent.label_,
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
            })
        return entities

    def extract_noun_phrases(self, doc: Doc) -> List[str]:
        """
        Extract noun phrases from document.

        Args:
            doc: spaCy Doc object

        Returns:
            List of noun phrase strings
        """
        return [chunk.text for chunk in doc.noun_chunks]

    def extract_tokens(self, doc: Doc) -> List[Dict[str, Any]]:
        """
        Extract token information from document.

        Args:
            doc: spaCy Doc object

        Returns:
            List of token dictionaries with text, lemma, POS, and dependencies
        """
        tokens = []
        for token in doc:
            tokens.append({
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "is_stop": token.is_stop,
            })
        return tokens

    def get_sentence_boundaries(self, doc: Doc) -> List[tuple]:
        """
        Get sentence boundaries from document.

        Args:
            doc: spaCy Doc object

        Returns:
            List of (start, end) tuples for each sentence
        """
        return [(sent.start_char, sent.end_char) for sent in doc.sents]

    def analyze_query_structure(self, doc: Doc) -> Dict[str, Any]:
        """
        Analyze the grammatical structure of the query.

        Args:
            doc: spaCy Doc object

        Returns:
            Dictionary with structural analysis
        """
        # Find root verb
        root_verb = None
        for token in doc:
            if token.dep_ == "ROOT":
                root_verb = token.text
                break

        # Find subjects and objects
        subjects = [token.text for token in doc if "subj" in token.dep_]
        objects = [token.text for token in doc if "obj" in token.dep_]

        # Find question words
        question_words = [
            token.text.lower() 
            for token in doc 
            if token.tag_ in ["WDT", "WP", "WP$", "WRB"]
        ]

        return {
            "root_verb": root_verb,
            "subjects": subjects,
            "objects": objects,
            "question_words": question_words,
            "is_question": any(
                token.tag_ in ["WDT", "WP", "WP$", "WRB"] 
                for token in doc
            ),
        }
