from .current import FW_MODEL_ID, FW_MODEL_SCHEMA

class IncompatibleDatasetError(RuntimeError):
    pass

def check_compat(meta: dict) -> None:
    got_schema = meta.get("fw_model_schema", None)
    if got_schema != FW_MODEL_SCHEMA:
        raise IncompatibleDatasetError(
            f"Incompatible fw_model_schema: got {got_schema}, expected {FW_MODEL_SCHEMA}"
        )

    got_id = meta.get("model_id", None)
    if got_id is not None and got_id != FW_MODEL_ID:
        raise IncompatibleDatasetError(
            f"Incompatible model_id: got {got_id!r}, expected {FW_MODEL_ID!r}"
        )
