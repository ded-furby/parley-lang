import json

from conftest import run_cli


def test_package_install_vendors_local_directory_and_lock(workdir, tmp_path):
    package = tmp_path / "mathkit"
    package.mkdir()
    (package / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")
    program = workdir / "uses_package.par"
    program.write_text('include "mathkit"\n\nto main:\n    say (double with 21)\n')

    install = run_cli(
        ["package", "install", "mathkit", str(package), "--version", "1.2.0"],
        cwd=workdir,
    )
    assert install.returncode == 0, install.stderr
    assert (workdir / "parley_modules" / "mathkit" / "main.par").is_file()
    lock = json.loads((workdir / "parley.lock.json").read_text())
    assert lock["packages"]["mathkit"]["version"] == "1.2.0"
    assert lock["packages"]["mathkit"]["path"] == "parley_modules/mathkit"

    check = run_cli(["check", program.name, "--json"], cwd=workdir)
    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)["ok"] is True


def test_package_list_reads_lockfile(workdir):
    (workdir / "parley.lock.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "packages": {
                    "mathkit": {
                        "version": "1.2.0",
                        "source": "../mathkit",
                        "path": "parley_modules/mathkit",
                    }
                },
            }
        )
    )

    proc = run_cli(["package", "list"], cwd=workdir)

    assert proc.returncode == 0, proc.stderr
    assert "mathkit 1.2.0 parley_modules/mathkit" in proc.stdout


def test_package_install_bad_source_keeps_existing_vendor(workdir):
    existing = workdir / "parley_modules" / "statkit"
    existing.mkdir(parents=True)
    (existing / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")

    proc = run_cli(
        ["package", "install", "statkit", "missing-package"],
        cwd=workdir,
    )

    assert proc.returncode == 1
    assert "package source does not exist" in proc.stderr
    assert (existing / "main.par").read_text().startswith("to double")


def test_package_install_rejects_path_like_name(workdir, tmp_path):
    package = tmp_path / "mathkit"
    package.mkdir()
    (package / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")

    proc = run_cli(
        ["package", "install", "../escape", str(package)],
        cwd=workdir,
    )

    assert proc.returncode == 1
    assert "package names may only contain" in proc.stderr
    assert not (workdir / "escape").exists()
