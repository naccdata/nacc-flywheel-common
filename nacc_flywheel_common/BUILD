python_sources(name="lib")

python_distribution(
    name="dist",
    dependencies=[":lib"],
    wheel=True,
    sdist=True,
    provides=python_artifact(
        name="nacc-flywheel-common",
        version="0.0.1",
        description="Common definitions for working with NACC Flywheel instances",
        author="NACC",
        author_email="nacchelp@uw.edu",
        url="https://github.com/naccdata/nacc-flywheel-common",
    ),
)