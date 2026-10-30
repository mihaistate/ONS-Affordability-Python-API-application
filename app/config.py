import os
import re
from dataclasses import dataclass


def duration_seconds(value: str) -> float:
    units = {'h': 3600, 'm': 60, 's': 1, 'ms': .001, 'us': .000001, 'µs': .000001, 'ns': .000000001}
    parts = re.findall(r'(\d+(?:\.\d+)?)(ms|us|µs|ns|h|m|s)', value)
    if not parts or ''.join(number + unit for number, unit in parts) != value:
        raise ValueError('POSTCODE_TIMEOUT must be a positive duration, e.g. 2s or 500ms')
    result = sum(float(number) * units[unit] for number, unit in parts)
    if result <= 0:
        raise ValueError('POSTCODE_TIMEOUT must be positive')
    return result


@dataclass(frozen=True)
class Settings:
    http_addr: str = ':8080'
    case_file: str = './data/case.json'
    ons_region_file: str = './data/ONSByRegion2019.xlsx'
    ons_composition_file: str = './data/ONSComposition2019.xlsx'
    postcode_base_url: str = 'https://api.postcodes.io'
    postcode_timeout: float = 2.0

    @classmethod
    def from_env(cls):
        defaults = cls()
        values = {key: os.getenv(key.upper()) or getattr(defaults, key)
                  for key in ('http_addr', 'case_file', 'ons_region_file', 'ons_composition_file', 'postcode_base_url')}
        return cls(**values, postcode_timeout=duration_seconds(os.getenv('POSTCODE_TIMEOUT') or '2s'))
