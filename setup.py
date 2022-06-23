import setuptools

if __name__ == "__main__":
    setuptools.setup(
        name="ztrack",
        version="0.3.3",
        entry_points={"console_scripts": ["ztrack=ztrack.cli:main"]},
        url="https://github.com/kclamar/ztrack",
    )
