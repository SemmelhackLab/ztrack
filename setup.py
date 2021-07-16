import setuptools

if __name__ == "__main__":
    setuptools.setup(
        name="ztrack",
        version="0.1.0",
        entry_points={"console_scripts": ["ztrack=ztrack.cli:main"]},
    )
