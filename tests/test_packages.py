import json

from conftest import REPO, run_cli


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


def test_package_new_creates_installable_package_skeleton(workdir):
    created = run_cli(["package", "new", "mathkit"], cwd=workdir)
    assert created.returncode == 0, created.stderr
    assert (workdir / "mathkit" / "main.par").is_file()

    install = run_cli(["package", "install", "mathkit", "mathkit"], cwd=workdir)
    assert install.returncode == 0, install.stderr

    program = workdir / "uses_new_package.par"
    program.write_text('include "mathkit"\n\nto main:\n    say package_ready\n')
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


def test_package_search_reads_registry_manifest(workdir, tmp_path):
    source = tmp_path / "registrykit-src"
    source.mkdir()
    (source / "main.par").write_text(
        "to triple with n as number giving number:\n    give back n times 3\n")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "registrykit": {
                "version": "1.2.3",
                "source": "registrykit-src",
                "description": "triples numbers",
            }
        },
    }))

    proc = run_cli(["package", "search", "--registry", str(registry)], cwd=workdir)

    assert proc.returncode == 0, proc.stderr
    assert "registrykit 1.2.3 triples numbers" in proc.stdout


def test_package_install_can_use_registry_entry(workdir, tmp_path):
    source = tmp_path / "registrymath-src"
    source.mkdir()
    (source / "main.par").write_text(
        "to triple with n as number giving number:\n    give back n times 3\n")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "registrymath": {
                "version": "1.2.3",
                "source": "registrymath-src",
                "description": "triples numbers",
            }
        },
    }))

    install = run_cli(
        ["package", "install", "registrymath", "--registry", str(registry)],
        cwd=workdir,
    )

    assert install.returncode == 0, install.stderr
    assert (workdir / "parley_modules" / "registrymath" / "main.par").is_file()
    lock = json.loads((workdir / "parley.lock.json").read_text())
    assert lock["packages"]["registrymath"]["version"] == "1.2.3"
    assert lock["packages"]["registrymath"]["registry"] == str(registry)

    program = workdir / "uses_registry_package.par"
    program.write_text('include "registrymath"\n\nto main:\n    say (triple with 7)\n')
    check = run_cli(["check", program.name, "--json"], cwd=workdir)
    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)["ok"] is True


def test_site_registry_manifest_can_install_package(workdir):
    registry = REPO / "site" / "registry.json"
    data = json.loads(registry.read_text())

    assert data["schema_version"] == 1
    assert "mathkit" in data["packages"]
    for entry in data["packages"].values():
        assert (registry.parent / entry["source"]).is_file()

    search = run_cli(["package", "search", "--registry", str(registry)], cwd=workdir)
    assert search.returncode == 0, search.stderr
    assert "mathkit" in search.stdout

    install = run_cli(["package", "install", "mathkit", "--registry", str(registry)], cwd=workdir)
    assert install.returncode == 0, install.stderr

    program = workdir / "uses_site_registry.par"
    program.write_text('include "mathkit"\n\nto main:\n    say (double with 21)\n')
    check = run_cli(["check", program.name, "--json"], cwd=workdir)
    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)["ok"] is True


def test_pages_deploy_script_publishes_registry_assets():
    script = (REPO / "scripts" / "deploy_pages.sh").read_text()

    assert "registry.json" in script
    assert "packages" in script


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
