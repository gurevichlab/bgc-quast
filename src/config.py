import time
from argparse import Namespace as CommandLineArgs
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import yaml


@dataclass
class OutputConfig:
    output_dir: Path
    symlink_to_latest: Path
    report: Path

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        # TODO: read these default values from config.yaml
        self.symlink_to_latest = self.output_dir / Path("latest")
        self.report = self.output_dir / Path("report.txt")
        self.html_report = self.output_dir / Path("report.html")
        self.tsv_report = self.output_dir / Path("report.tsv")


@dataclass
class ProductMappingConfig:
    product_yamls: Dict[str, Path]


@dataclass
class Config:
    magic_number: int  # just a placeholder for future expansion of the config
    magic_str: str  # just a placeholder for future expansion of the config
    output_config: OutputConfig
    product_mapping_config: ProductMappingConfig
    bgc_completeness_margin: int
    allowed_gap_for_fragmented_recovery: int
    compare_tools_overlap_threshold: float = 0.9


def get_default_output_dir(cfg: dict) -> Path:
    while (
        out_dir := (
            Path.cwd()
            / Path(cfg["default_output_dir_root"])
            / Path(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        )
    ).exists():
        time.sleep(1)

    return out_dir


def load_config(args: Optional[CommandLineArgs] = None) -> Config:
    tool_dir = Path(__file__).parent.parent.resolve()
    configs_dir = tool_dir / Path("configs")
    cfg = yaml.safe_load((configs_dir / "config.yaml").open("r"))
    out_dir = (
        args.output_dir.resolve()
        if args is not None and args.output_dir is not None
        else get_default_output_dir(cfg)
    )
    product_mapping_config = ProductMappingConfig(
        product_yamls={
            k: configs_dir / Path(v) for k, v in cfg["product_yamls"].items()
        }
    )

    conf = Config(
        magic_number=42,
        magic_str="",
        output_config=OutputConfig(out_dir),
        product_mapping_config=product_mapping_config,
        bgc_completeness_margin=cfg["bgc_completeness_margin"],
        allowed_gap_for_fragmented_recovery=cfg["allowed_gap_for_fragmented_recovery"],
        # compare_tools_overlap_threshold stays at dataclass default (0.9) unless overridden by CLI below
    )

    # --- NEW: CLI override (only if user provided --overlap-threshold/--thr) ---
    if args is not None and getattr(args, "compare_tools_overlap_threshold", None) is not None:
        conf.compare_tools_overlap_threshold = args.compare_tools_overlap_threshold

    return conf