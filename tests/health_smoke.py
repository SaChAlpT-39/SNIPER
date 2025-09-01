from modules_utils.health import run_health_checks
from pathlib import Path

if __name__ == '__main__':
    rpt = run_health_checks(Path('.'))
    print('OK:', rpt.ok)
    for k, v in rpt.details.items():
        print(f' - {k}: {v}')
