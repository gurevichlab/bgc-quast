import time
import yaml
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.option_parser import CommandLineArgs


@dataclass
class OutputConfig:
    output_dir: Path
    symlink_to_latest: Path
    report: Path

    def __init__(self,
                 output_dir: Path):
        self.output_dir = output_dir
        # TODO: read these default values from config.yaml
        self.symlink_to_latest = self.output_dir / Path('latest')
        self.report = self.output_dir / Path('report.txt')
        self.html_report = self.output_dir / Path('report.html')


@dataclass
class Config:
    magic_number: int  # just a placeholder for future expansion of the config
    magic_str: str     # just a placeholder for future expansion of the config
    output_config: OutputConfig


def get_default_output_dir(cfg: dict) -> Path:
    while (out_dir := (Path.cwd() / Path(cfg['default_output_dir_root']) /
                       Path(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))).exists():
        time.sleep(1)

    return out_dir


def load_config(args: Optional[CommandLineArgs] = None) -> Config:
    tool_dir = Path(__file__).parent.parent.resolve()
    configs_dir = tool_dir / Path('configs')
    cfg = yaml.safe_load((configs_dir / 'config.yaml').open('r'))
    out_dir = args.output_dir.resolve() \
        if args is not None and args.output_dir is not None else get_default_output_dir(cfg)

    return Config(magic_number=42, magic_str='', output_config=OutputConfig(out_dir))
