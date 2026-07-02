"""Huawei parameter catalog helpers for NetGenix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParameterDefinition:
    key: str
    label: str
    unit: str
    command: str
    field: str
    category: str
    priority: int
    value_type: str = "string"
    description: str = ""


TOP_5_PARAMETERS: tuple[ParameterDefinition, ...] = (
    ParameterDefinition(
        "reference_signal_power_pdschcfg",
        "Signal Power",
        "dBm",
        "LST PDSCHCFG: LOCALCELLID=1;",
        "Reference signal power(0.1dBm)",
        "RF",
        1,
        "number",
        "Reference signal power / coverage control.",
    ),
    ParameterDefinition(
        "a3_event_offset",
        "A3 Offset",
        "dB",
        "LST UECOOPERATIONPARA:;",
        "A3 Handover Threshold Offset",
        "Mobility",
        2,
        "number",
        "Neighbor-cell handover trigger offset.",
    ),
    ParameterDefinition(
        "t310_timer",
        "T310 Timer",
        "ms",
        "LST UETIMERCONST:;",
        "Timer 310",
        "RLF",
        3,
        "number",
        "Radio link failure detection timer.",
    ),
    ParameterDefinition(
        "p0_nominal_pusch",
        "P0 PUSCH",
        "dBm",
        "LST CELLULPCCOMM: LOCALCELLID=1;",
        "P0 nominal PUSCH(dBm)",
        "Uplink",
        4,
        "number",
        "Uplink shared channel nominal power baseline.",
    ),
    ParameterDefinition(
        "pdcch_aggregation_level",
        "PDCCH Agg",
        "",
        "LST CELLPDCCHALGO: LOCALCELLID=1;",
        "SignalCongregateLevel",
        "PDCCH",
        5,
        description="Control-channel aggregation/congregation level.",
    ),
)


TOP_15_PARAMETERS = TOP_5_PARAMETERS
PARAMETER_BY_KEY = {parameter.key: parameter for parameter in TOP_5_PARAMETERS}


DISCOVERY_COMMANDS: dict[str, str] = {
    "version": "LST VER:;",
    "cell_all": "LST CELL:;",
    "cell_1": "LST CELL: LOCALCELLID=1;",
    "board": "DSP BRD:;",
    "sctp_link": "LST SCTPLNK:;",
    "ip_path": "LST IPPATH:;",
    "route": "LST IPRT:;",
    "vlan": "LST VLANMAP:;",
    "cell_op": "DSP CELL:;",
    "cell_dl_pc": "LST CELLDLPCPDSCHPA: LOCALCELLID=1;",
    "cell_ul_pc_common": "LST CELLULPCCOMM: LOCALCELLID=1;",
    "pdsch_cfg": "LST PDSCHCFG: LOCALCELLID=1;",
    "cell_pdcch_algo": "LST CELLPDCCHALGO: LOCALCELLID=1;",
    "pucch_cfg": "LST PUCCHCFG: LOCALCELLID=1;",
    "srs_cfg": "LST SRSCFG: LOCALCELLID=1;",
    "phich_cfg": "LST PHICHCFG: LOCALCELLID=1;",
    "drx_cfg": "LST DRX:;",
    "rrc_conn_ctrl": "LST RRCCONNSTATETIMER:;",
    "ue_timer_const": "LST UETIMERCONST:;",
    "ue_cooperation": "LST UECOOPERATIONPARA:;",
    "intra_freq_ho": "LST INTRAFREQHOGROUP:;",
    "inter_freq_ho": "LST INTERFREQHOGROUP:;",
    "eutran_intra_neighbor": "LST EUTRANINTRAFREQNCELL:;",
    "eutran_inter_neighbor": "LST EUTRANINTERFREQNCELL:;",
    "external_eutran_cell": "LST EUTRANEXTERNALCELL:;",
    "anr": "LST ANR:;",
    "x2": "LST X2:;",
    "mro": "LST MRO:;",
}


def command_key(command: str) -> str:
    return " ".join(command.strip().upper().split())


def top_15_commands() -> list[str]:
    seen = set()
    commands = []
    for parameter in TOP_15_PARAMETERS:
        key = command_key(parameter.command)
        if key in seen:
            continue
        seen.add(key)
        commands.append(parameter.command)
    return commands


def coerce_parameter_value(value: Any, value_type: str) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if value_type != "number":
        return text
    import re

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return text
    number = float(match.group(0))
    return int(number) if number.is_integer() else number
