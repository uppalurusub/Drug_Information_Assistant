import time

from langsmith import traceable

from app.prompts.drug_prompt import drug_prompt
from app.schemas.response_model import DrugResponse
from app.utils.vector_store import load_vectorstore
from app.config.settings import settings
logger = settings.get_logger()

from app.utils.langsmith_usage import LLMUsageCapture


class DrugImplementation:
    def __init__(self):
        logger.info("Initializing DrugImplementation")
        self.llm = settings.get_model_client()
        self.vectorstore = load_vectorstore()
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self.last_usage = {}
        self.last_timings = {}
        # Reuse the wrapper rather than recreating it on every request.
        self.structured_llm = self.llm.with_structured_output(
            DrugResponse, method="function_calling", strict=False
        )

    @traceable(name="drug-information-rag", run_type="chain", tags=["healthcare", "drug-information", "rag"])
    def get_drug_information(self, drug_name: str) -> DrugResponse:
        request_started = time.perf_counter()
        capture = LLMUsageCapture()
        timings = {}
        try:
            retrieval_started = time.perf_counter()
            docs = self.retriever.invoke(drug_name)
            timings["retrieval_seconds"] = round(time.perf_counter() - retrieval_started, 4)

            prompt_started = time.perf_counter()
            context = "\n\n".join(doc.page_content for doc in docs)
            prompt_value = drug_prompt.invoke({"context": context, "drug_name": drug_name})
            timings["prompt_build_seconds"] = round(time.perf_counter() - prompt_started, 4)

            llm_started = time.perf_counter()
            response = self.structured_llm.invoke(
                prompt_value,
                config={
                    "callbacks": [capture],
                    "tags": ["healthcare", "drug-information", "openrouter"],
                    "run_name": "drug-information-llm",
                    "metadata": {"feature": "drug-information", "provider": "openrouter"},
                },
            )
            timings["llm_seconds"] = round(time.perf_counter() - llm_started, 4)
            self.last_usage = dict(capture.data)
            logger.info("LLM usage telemetry: {}", self.last_usage)
            return response
        except Exception as ex:
            self.last_usage = dict(capture.data)
            logger.exception("Error while processing drug '{}'", drug_name)
            return DrugResponse(
                drug_name=drug_name, usage="Information could not be generated.",
                dosage="Consult a qualified healthcare professional or pharmacist.",
                side_effects=[], status="FAILED",
            )
        finally:
            timings["implementation_seconds"] = round(time.perf_counter() - request_started, 4)
            self.last_timings = timings
            logger.info("Drug request timings: {}", timings)
