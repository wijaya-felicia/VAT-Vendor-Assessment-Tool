from functools import lru_cache
from src.modules.data_pipeline import DataPipeline

@lru_cache
def get_data_pipeline() -> DataPipeline:
    return DataPipeline()