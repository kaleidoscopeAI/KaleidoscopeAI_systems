import logging
from .quantum import QuantumConsciousness
from .engines import KaleidoscopeEngine, PerspectiveEngine

logger = logging.getLogger(__name__)

class AIChatbot:
    def __init__(self):
        self.quantum = QuantumConsciousness()
        self.supernodes = []

    def respond(self, query):
        try:
            quantum_response = self.quantum.process_query(query)
            response = f"**Kaleidoscope AI Response:**\n{quantum_response}"
            logger.info(f"Chatbot generated response for query: '{query}'")
            return response
        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            return "Error generating response."

    def register_supernode(self, supernode):
        self.supernodes.append(supernode)
        logger.info(f"Registered SuperNode: {supernode.id}")

