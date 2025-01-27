import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True


RQ_VERSIONS = ["2.0.0", "2.1.0", None]
DISHKA_VERSIONS = ["1.4.2", None]
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]


def install_command(dependency: str, version: str | None = None):
    """Return install command for a specific dependency."""
    return f"{dependency}=={version}" if version else dependency


def load_dev_dependencies() -> list[str]:
    """Load development dependencies from pyproject.toml."""
    toml_data = nox.project.load_toml("pyproject.toml")
    return toml_data["dependency-groups"]["dev"]


@nox.session(python=PYTHON_VERSIONS, tags=["unit"])
@nox.parametrize("rq_version", RQ_VERSIONS)
@nox.parametrize("dishka_version", DISHKA_VERSIONS)
def tests(session: nox.Session, rq_version: str | None, dishka_version: str | None):
    """Run tests with different versions of dependencies."""

    session.install(install_command("dishka", dishka_version))
    session.install(install_command("rq", rq_version))

    dev_deps = load_dev_dependencies()
    session.install(*dev_deps)

    toml_data = nox.project.load_toml("pyproject.toml")
    dev_deps = toml_data["dependency-groups"]["dev"]

    session.install(*dev_deps)

    session.install("-e", ".")

    session.run(
        "pytest",
        "tests/unit",
        "--cov=dishka_rq",
        "--cov-report=term-missing",
        "--cov-append",
        "--cov-config=.coveragerc",
        env={
            "COVERAGE_FILE": f".coverage.{session.name}",
        },
        *session.posargs,
    )


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate and view coverage report."""
    session.install("coverage")
    session.run("coverage", "combine")
    session.run("coverage", "report", "--fail-under=100")
