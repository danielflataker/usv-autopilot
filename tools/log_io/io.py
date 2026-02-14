from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from .layout import (
    DEFAULT_RECORD_LAYOUTS,
    ENDIAN_LITTLE,
    FILE_HEADER_STRUCT,
    MAGIC,
    RECORD_HEADER_STRUCT,
    RecordLayout,
)


@dataclass(frozen=True, slots=True)
class TimeseriesHeader:
    magic: str
    fw_model_schema: int
    endianness: str
    t0_us: int


@dataclass(frozen=True, slots=True)
class UnknownRecord:
    t_us: int
    type_id: int
    payload_len: int


@dataclass(frozen=True, slots=True)
class TimeseriesData:
    header: TimeseriesHeader
    records: dict[str, dict[str, np.ndarray]]
    record_counts: dict[str, int]
    unknown_records: tuple[UnknownRecord, ...]


def _normalize_layouts(
    record_layouts: Mapping[int, RecordLayout] | None,
) -> Mapping[int, RecordLayout]:
    return DEFAULT_RECORD_LAYOUTS if record_layouts is None else record_layouts


def read_timeseries_bin(
    path: str | Path,
    *,
    record_layouts: Mapping[int, RecordLayout] | None = None,
    strict_payload_len: bool = True,
    keep_unknown: bool = True,
) -> TimeseriesData:
    """Read TLV timeseries binary into structured numpy arrays.

    Args:
        path: Path to `timeseries.bin`.
        record_layouts: Optional record decoder map. Unknown type IDs are skipped.
        strict_payload_len: If True, mismatched payload size for known record raises.
        keep_unknown: If True, collect unknown record metadata.

    Returns:
        Parsed timeseries data with header, decoded records, and counts.
    """
    layouts = _normalize_layouts(record_layouts)
    data = Path(path).read_bytes()
    if len(data) < FILE_HEADER_STRUCT.size:
        raise ValueError(
            f"timeseries file too small: {len(data)} bytes, expected at least {FILE_HEADER_STRUCT.size}"
        )

    magic_raw, fw_model_schema, endianness_id, t0_us = FILE_HEADER_STRUCT.unpack_from(data, 0)
    if magic_raw != MAGIC:
        raise ValueError(f"invalid magic: got {magic_raw!r}, expected {MAGIC!r}")
    if endianness_id != ENDIAN_LITTLE:
        raise ValueError(f"unsupported endianness id: {endianness_id}")

    header = TimeseriesHeader(
        magic=MAGIC.decode("ascii"),
        fw_model_schema=int(fw_model_schema),
        endianness="little",
        t0_us=int(t0_us),
    )

    raw_buffers: dict[str, dict[str, list[float | int]]] = {}
    record_counts: dict[str, int] = {}
    unknown_records: list[UnknownRecord] = []

    offset = FILE_HEADER_STRUCT.size
    n = len(data)
    while offset < n:
        if offset + RECORD_HEADER_STRUCT.size > n:
            raise ValueError(f"truncated record header at byte offset {offset}")

        t_us, rec_type, payload_len = RECORD_HEADER_STRUCT.unpack_from(data, offset)
        offset += RECORD_HEADER_STRUCT.size
        payload_end = offset + int(payload_len)
        if payload_end > n:
            raise ValueError(
                f"truncated payload for type={rec_type} at byte offset {offset}: "
                f"need {payload_len}, have {n - offset}"
            )

        layout = layouts.get(int(rec_type))
        if layout is None:
            if keep_unknown:
                unknown_records.append(
                    UnknownRecord(t_us=int(t_us), type_id=int(rec_type), payload_len=int(payload_len))
                )
            offset = payload_end
            continue

        expected_len = layout.payload_struct.size
        if strict_payload_len and payload_len != expected_len:
            raise ValueError(
                f"payload length mismatch for {layout.name} (type={rec_type}): "
                f"got {payload_len}, expected {expected_len}"
            )
        if payload_len < expected_len:
            raise ValueError(
                f"payload too short for {layout.name} (type={rec_type}): "
                f"got {payload_len}, expected at least {expected_len}"
            )

        if layout.name not in raw_buffers:
            raw_buffers[layout.name] = {"t_us": []}
            for field in layout.fields:
                raw_buffers[layout.name][field] = []
            record_counts[layout.name] = 0

        unpacked = layout.payload_struct.unpack_from(data, offset)
        bucket = raw_buffers[layout.name]
        bucket["t_us"].append(int(t_us))
        for field, value in zip(layout.fields, unpacked):
            bucket[field].append(value)
        record_counts[layout.name] += 1

        offset = payload_end

    arrays: dict[str, dict[str, np.ndarray]] = {}
    for name, values in raw_buffers.items():
        out: dict[str, np.ndarray] = {"t_us": np.asarray(values["t_us"], dtype=np.uint64)}
        for field, series in values.items():
            if field == "t_us":
                continue
            out[field] = np.asarray(series)
        arrays[name] = out

    return TimeseriesData(
        header=header,
        records=arrays,
        record_counts=record_counts,
        unknown_records=tuple(unknown_records),
    )

