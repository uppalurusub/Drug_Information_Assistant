import os
import time
from datetime import datetime
import mlflow
from langsmith import traceable
from app.config.settings import settings
logger = settings.get_logger()
from app.implementations.drug_impl import DrugImplementation
from app.schemas.response_model import DrugResponse

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "Drug_Information_Assistant"))


class DrugService:
    def __init__(self):
        self.drug_impl = DrugImplementation()

    @mlflow.trace(name="Drug_Information_Assistant")
    
    def get_drug_information(self, drug_name: str) -> DrugResponse:
        started = time.perf_counter()
        start_time = datetime.now()
        if not drug_name or not drug_name.strip():
            raise ValueError("Drug name cannot be empty")
        drug_name = drug_name.strip()
        response = None
        try:
            with mlflow.start_run(run_name=f"drug-information-{datetime.now():%Y%m%d_%H%M%S}"):
                mlflow.log_param("input_drug_name", drug_name)
                
                mlflow.set_tag("source", "FastAPI")
                mlflow.set_tag("endpoint", "/drug/information")
                response = self.drug_impl.get_drug_information(drug_name)
                usage = self.drug_impl.last_usage or {}
                timings = self.drug_impl.last_timings or {}
                # Avoid logging full prompt/context or sensitive user data to MLflow.
                for metric, key in [
                    ("input_tokens", "input_tokens"), ("output_tokens", "output_tokens"),
                    ("total_tokens", "total_tokens"),
                ]:
                    mlflow.log_metric(metric, float(usage.get(key) or 0))
                for metric, key in [
                    ("input_cost_usd", "input_cost"), ("output_cost_usd", "output_cost"),
                    ("total_cost_usd", "total_cost"),
                ]:
                    if usage.get(key) is not None:
                        mlflow.log_metric(metric, float(usage[key]))
                mlflow.log_metric("execution_time_seconds", round(time.perf_counter() - started, 4))
                mlflow.log_param("output", response)
                for metric, value in timings.items():
                    mlflow.log_metric(metric, float(value))
                mlflow.set_tag("usage_source", usage.get("usage_source", "unavailable"))
                mlflow.set_tag("llm_model", str(usage.get("model_name") or os.getenv("fallback_model_2", "unknown")))
                mlflow.log_param("started_at", start_time.strftime("%Y-%m-%d %H:%M:%S"))
                mlflow.log_param("response_status", getattr(response, "status", "SUCCESS"))
            if getattr(response, "status", "SUCCESS") == "FAILED":
                logger.warning("Drug information request failed to generate a valid response for {}", drug_name)
            else:
                logger.success("Successfully processed drug information for {}", drug_name)
            return response
        except Exception:
            logger.exception("Error in DrugService for drug: {}", drug_name)
            return DrugResponse(
                drug_name=drug_name, usage="N/A", dosage="N/A",
                side_effects=[], status="FAILED",
            )
