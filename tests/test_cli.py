import json

from conftest import run_cli
from parley import __version__


def test_doctor_json_reports_ready_toolchain(workdir):
    proc = run_cli(["doctor", "--json"], cwd=workdir)

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert report["version"] == __version__

    checks = {check["name"]: check for check in report["checks"]}
    assert checks["parley"]["ok"] is True
    assert checks["python"]["ok"] is True
    assert checks["cargo"]["ok"] is True
    assert checks["stdlib"]["ok"] is True
    assert checks["packages"]["ok"] is True
    for package in ["std/math", "std/text", "std/list", "std/map"]:
        assert package in checks["stdlib"]["detail"]
