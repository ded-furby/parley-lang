import hashlib
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


def test_package_install_rejects_invalid_version(workdir, tmp_path):
    package = tmp_path / "invalidkit"
    package.mkdir()
    (package / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")

    install = run_cli(
        ["package", "install", "invalidkit", str(package), "--version", "latest"],
        cwd=workdir,
    )

    assert install.returncode == 1
    assert "package versions must use semantic version form X.Y.Z" in install.stderr
    assert not (workdir / "parley_modules" / "invalidkit").exists()


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
                "license": "MIT",
                "maintainer": "Registry Team <https://example.com>",
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


def test_package_install_verifies_registry_sha256_and_records_lock(workdir, tmp_path):
    source = tmp_path / "signedmath"
    source.mkdir()
    content = "to double with n as number giving number:\n    give back n times 2\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "signedmath": {
                "version": "2.0.0",
                "source": "signedmath",
                "description": "doubles numbers",
                "sha256": sha256,
            }
        },
    }))

    install = run_cli(
        ["package", "install", "signedmath", "--registry", str(registry)],
        cwd=workdir,
    )

    assert install.returncode == 0, install.stderr
    lock = json.loads((workdir / "parley.lock.json").read_text())
    assert lock["packages"]["signedmath"]["sha256"] == sha256


def test_package_install_rejects_registry_sha256_mismatch_without_overwriting(workdir, tmp_path):
    existing = workdir / "parley_modules" / "badmath"
    existing.mkdir(parents=True)
    (existing / "main.par").write_text("to value giving number:\n    give back 1\n")
    source = tmp_path / "badmath"
    source.mkdir()
    (source / "main.par").write_text("to value giving number:\n    give back 2\n")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "badmath": {
                "version": "2.0.0",
                "source": "badmath",
                "description": "changed package",
                "sha256": "0" * 64,
            }
        },
    }))

    install = run_cli(
        ["package", "install", "badmath", "--registry", str(registry)],
        cwd=workdir,
    )

    assert install.returncode == 1
    assert "sha256 mismatch" in install.stderr
    assert "give back 1" in (existing / "main.par").read_text()


def test_package_publish_prints_registry_entry_with_sha256(workdir, tmp_path):
    source = tmp_path / "mathkit"
    source.mkdir()
    content = "to double with n as number giving number:\n    give back n times 2\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()

    publish = run_cli(
        [
            "package", "publish", "mathkit", str(source),
            "--version", "1.2.3",
            "--description", "small math helpers",
            "--license", "MIT",
            "--maintainer", "Arjun Avtani <https://github.com/ded-furby>",
        ],
        cwd=workdir,
    )

    assert publish.returncode == 0, publish.stderr
    payload = json.loads(publish.stdout)
    assert payload["name"] == "mathkit"
    assert payload["entry"] == {
        "version": "1.2.3",
        "source": "packages/mathkit",
        "description": "small math helpers",
        "license": "MIT",
        "maintainer": "Arjun Avtani <https://github.com/ded-furby>",
        "sha256": sha256,
    }


def test_package_publish_rejects_invalid_version(workdir, tmp_path):
    source = tmp_path / "mathkit"
    source.mkdir()
    (source / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")

    publish = run_cli(
        [
            "package", "publish", "mathkit", str(source),
            "--version", "1",
            "--description", "small math helpers",
            "--license", "MIT",
            "--maintainer", "Arjun Avtani <https://github.com/ded-furby>",
        ],
        cwd=workdir,
    )

    assert publish.returncode == 1
    assert "package versions must use semantic version form X.Y.Z" in publish.stderr


def test_package_review_accepts_valid_submission(workdir, tmp_path):
    source = tmp_path / "reviewkit"
    source.mkdir()
    content = "to double with n as number giving number:\n    give back n times 2\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()

    review = run_cli(
        [
            "package", "review", "reviewkit", str(source),
            "--version", "1.2.3",
            "--description", "reviewed math helpers",
            "--license", "MIT",
            "--maintainer", "Arjun Avtani <https://github.com/ded-furby>",
        ],
        cwd=workdir,
    )

    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["ok"] is True
    assert payload["name"] == "reviewkit"
    assert payload["entry"]["sha256"] == sha256
    assert payload["entry"]["source"] == "packages/reviewkit"
    assert payload["review"]["parley_files"] == ["main.par"]


def test_package_review_rejects_syntax_errors(workdir, tmp_path):
    source = tmp_path / "badkit"
    source.mkdir()
    (source / "main.par").write_text("to broken\n    say \"bad\"\n")

    review = run_cli(
        [
            "package", "review", "badkit", str(source),
            "--version", "1.0.0",
            "--description", "broken package",
            "--license", "MIT",
            "--maintainer", "Arjun Avtani <https://github.com/ded-furby>",
        ],
        cwd=workdir,
    )

    assert review.returncode == 1
    assert "main.par" in review.stderr
    assert "P101" in review.stderr


def test_package_verify_accepts_locked_package(workdir, tmp_path):
    source = tmp_path / "mathkit"
    source.mkdir()
    (source / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")
    install = run_cli(
        ["package", "install", "mathkit", str(source), "--version", "1.2.0"],
        cwd=workdir,
    )
    assert install.returncode == 0, install.stderr

    verify = run_cli(["package", "verify"], cwd=workdir)

    assert verify.returncode == 0, verify.stderr
    assert "OK mathkit 1.2.0 parley_modules/mathkit" in verify.stdout


def test_package_verify_rejects_modified_vendor(workdir, tmp_path):
    source = tmp_path / "mathkit"
    source.mkdir()
    (source / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")
    install = run_cli(
        ["package", "install", "mathkit", str(source), "--version", "1.2.0"],
        cwd=workdir,
    )
    assert install.returncode == 0, install.stderr
    (workdir / "parley_modules" / "mathkit" / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 3\n")

    verify = run_cli(["package", "verify"], cwd=workdir)

    assert verify.returncode == 1
    assert "sha256 mismatch for mathkit" in verify.stderr


def test_package_verify_rejects_missing_digest(workdir):
    package = workdir / "parley_modules" / "legacy"
    package.mkdir(parents=True)
    (package / "main.par").write_text("to ready giving yesno:\n    give back yes\n")
    (workdir / "parley.lock.json").write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "legacy": {
                "version": "0.1.0",
                "source": "../legacy",
                "path": "parley_modules/legacy",
            }
        },
    }))

    verify = run_cli(["package", "verify"], cwd=workdir)

    assert verify.returncode == 1
    assert "legacy has no sha256 in parley.lock.json" in verify.stderr


def test_package_check_registry_accepts_checksum_manifest(workdir, tmp_path):
    source = tmp_path / "registrykit-src"
    source.mkdir()
    content = "to triple with n as number giving number:\n    give back n times 3\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "registrykit": {
                "version": "1.2.3",
                "source": "registrykit-src",
                "description": "triples numbers",
                "license": "MIT",
                "maintainer": "Registry Team <https://example.com>",
                "sha256": sha256,
            }
        },
    }))

    check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)

    assert check.returncode == 0, check.stderr
    assert "OK registrykit 1.2.3 registrykit-src" in check.stdout


def test_package_check_registry_rejects_bad_checksum(workdir, tmp_path):
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
                "license": "MIT",
                "maintainer": "Registry Team <https://example.com>",
                "sha256": "0" * 64,
            }
        },
    }))

    check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)

    assert check.returncode == 1
    assert "sha256 mismatch for registrykit" in check.stderr


def test_package_check_registry_requires_sha256(workdir, tmp_path):
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
                "license": "MIT",
                "maintainer": "Registry Team <https://example.com>",
            }
        },
    }))

    check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)

    assert check.returncode == 1
    assert "registrykit has no sha256" in check.stderr


def test_package_check_registry_requires_license_and_maintainer(workdir, tmp_path):
    source = tmp_path / "registrykit-src"
    source.mkdir()
    content = "to triple with n as number giving number:\n    give back n times 3\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "registrykit": {
                "version": "1.2.3",
                "source": "registrykit-src",
                "description": "triples numbers",
                "sha256": sha256,
            }
        },
    }))

    check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)

    assert check.returncode == 1
    assert "registrykit registry entry is missing license" in check.stderr
    assert "registrykit registry entry is missing maintainer" in check.stderr


def test_package_check_registry_rejects_invalid_version(workdir, tmp_path):
    source = tmp_path / "registrykit-src"
    source.mkdir()
    content = "to triple with n as number giving number:\n    give back n times 3\n"
    (source / "main.par").write_text(content)
    sha256 = hashlib.sha256(b"main.par\0" + content.encode()).hexdigest()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "packages": {
            "registrykit": {
                "version": "latest",
                "source": "registrykit-src",
                "description": "triples numbers",
                "license": "MIT",
                "maintainer": "Registry Team <https://example.com>",
                "sha256": sha256,
            }
        },
    }))

    check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)

    assert check.returncode == 1
    assert "registrykit version latest is invalid" in check.stderr


def test_site_registry_manifest_can_install_package(workdir):
    registry = REPO / "site" / "registry.json"
    data = json.loads(registry.read_text())

    assert data["schema_version"] == 1
    assert "mathkit" in data["packages"]
    for entry in data["packages"].values():
        source = registry.parent / entry["source"]
        assert source.is_file()
        assert entry["license"] == "MIT"
        assert entry["maintainer"] == "Arjun Avtani <https://github.com/ded-furby>"
        expected = hashlib.sha256(b"main.par\0" + source.read_bytes()).hexdigest()
        assert entry["sha256"] == expected

    registry_check = run_cli(["package", "check-registry", str(registry)], cwd=workdir)
    assert registry_check.returncode == 0, registry_check.stderr

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
