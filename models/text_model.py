from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine, OperatorConfig
from presidio_analyzer.nlp_engine import SpacyNlpEngine
import spacy

from googletrans import Translator
import langid

tranlator = Translator()

try:
    nlp = spacy.load("ru_core_news_sm")
    print("spaCy model 'ru_core_news_sm' loaded successfully.")
except OSError:
    import spacy.cli
    spacy.cli.download("ru_core_news_sm")
    nlp = spacy.load("ru_core_news_sm")

class LoadedSpacyNlpEngine(SpacyNlpEngine):
    def __init__(self, loaded_spacy_model):
        super().__init__()  
        self.nlp = {"ru": loaded_spacy_model}

nlp_engine = LoadedSpacyNlpEngine(loaded_spacy_model=nlp)

try:
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    print("AnalyzerEngine initialized successfully.")
except Exception as e:
    print(f"Error initializing AnalyzerEngine: {e}")

anonymizer = AnonymizerEngine()

custom_patterns = [
    PatternRecognizer(supported_entity="IIN", patterns=[Pattern(name="IIN Pattern", regex=r"\b\d{12}\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="IPN", patterns=[Pattern(name="IPN Pattern", regex=r"\b\d{12}\b", score=0.95)], supported_language="ru"),
    PatternRecognizer(supported_entity="Bank Account", patterns=[Pattern(name="Account Pattern", regex=r"\b\d{20}\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="Credit Card", patterns=[Pattern(name="Card Pattern", regex=r"\b\d{16}\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="SWIFT Code", patterns=[Pattern(name="SWIFT Pattern", regex=r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="Phone Number", patterns=[Pattern(name="Phone Pattern", regex=r"\+7\d{10}", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="Email", patterns=[Pattern(name="Email Pattern", regex=r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="IP Address", patterns=[Pattern(name="IP Pattern", regex=r"\b(?:\d{1,3}\.){3}\d{1,3}\b", score=1.0)], supported_language="ru"),
    PatternRecognizer(supported_entity="Passport", patterns=[Pattern(name="Passport Pattern", regex=r"\b\d{9}\b", score=0.95)], supported_language="ru"),
    PatternRecognizer(supported_entity="Address", patterns=[Pattern(name="Address Pattern", regex=r"\b(?:ул\.|улица|пер\.|переулок|пр\.|проспект|мкр\.|микрорайон|г\.|город|с\.|село|д\.|деревня|обл\.|область)\s?[А-Яа-я\s\d.,-]+", score=0.8)], supported_language="ru")
]

for rec in custom_patterns:
    analyzer.registry.add_recognizer(rec)

def anonymize_text(text: str) -> str:
    lang, _ = langid.classify(text)

    if lang == 'kk':
        text = tranlator.translate(text, src='kk', dest='ru').text

    try:
        results = analyzer.analyze(text=text, language="ru")
        
        operators = {
            "IIN": OperatorConfig("replace", {"new_value": "[IIN_ЗАМЕНЕНО]"})
        }
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)

        if lang == 'kk':
            anonymized.text = tranlator.translate(text, src="ru", dest='kk').text

        return anonymized.text
    except Exception as e:
        print(f"Error anonymizing text: {e}")
        return text
