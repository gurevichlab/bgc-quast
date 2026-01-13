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
    latest_symlink: Path
    update_latest_symlink: bool

    report: Path
    html_report: Path
    tsv_report: Path


@dataclass
class ProductMappingConfig:
    product_yamls: Dict[str, Path]


@dataclass
class Config:
    output_config: OutputConfig
    product_mapping_config: ProductMappingConfig
    allowed_gap_for_fragmented_recovery: int
    min_bgc_length: int
    bgc_completeness_margin: int
    compare_tools_overlap_threshold: float


def _unique_timestamp_dir(root: Path) -> Path:
    while True:
        out_dir = root / Path(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        if not out_dir.exists():
            return out_dir
        time.sleep(1)


def load_config(args: Optional[CommandLineArgs] = None) -> Config:
    tool_dir = Path(__file__).parent.parent.resolve()
    configs_dir = tool_dir / Path("configs")
    cfg = yaml.safe_load((configs_dir / "config.yaml").open("r"))

    default_output_dir_root = Path.cwd() / Path(cfg["default_output_dir_root"])
    latest_output_dir_symlink = default_output_dir_root / Path(cfg["symlink_to_latest"])

    if args is not None and getattr(args, "output_dir", None) is not None:
        output_dir = args.output_dir.expanduser().resolve()
        update_latest = False
    else:
        output_dir = _unique_timestamp_dir(default_output_dir_root)
        update_latest = True

    output_config = OutputConfig(
        output_dir=output_dir,
        latest_symlink=latest_output_dir_symlink,
        update_latest_symlink=update_latest,
        report=output_dir / Path(cfg["report_txt"]),
        html_report=output_dir / Path(cfg["report_html"]),
        tsv_report=output_dir / Path(cfg["report_tsv"]),
    )

    product_mapping_config = ProductMappingConfig(
        product_yamls={
            k: configs_dir / Path(v) for k, v in cfg["product_yamls"].items()
        }
    )

    conf = Config(
        output_config=output_config,
        product_mapping_config=product_mapping_config,
        min_bgc_length=cfg["min_bgc_length"],
        bgc_completeness_margin=cfg["bgc_completeness_margin"],
        allowed_gap_for_fragmented_recovery=cfg["allowed_gap_for_fragmented_recovery"],
        compare_tools_overlap_threshold=cfg["compare_tools_overlap_threshold"],
    )

    # CLI override
    if args is not None and getattr(args, "compare_tools_overlap_threshold", None) is not None:
        conf.compare_tools_overlap_threshold = args.compare_tools_overlap_threshold

    if args is not None and getattr(args, "bgc_completeness_margin", None) is not None:
        conf.bgc_completeness_margin = args.bgc_completeness_margin

    if args is not None and getattr(args, "min_bgc_length", None) is not None:
        conf.min_bgc_length = args.min_bgc_length

    return conf
