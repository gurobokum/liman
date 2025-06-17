import nox


@nox.session
def test(session: nox.Session) -> None:
    session.install("pytest", "pytest-cov")
    session.run("pytest", "tests")
