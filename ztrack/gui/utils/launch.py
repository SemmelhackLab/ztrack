import sys
from pathlib import Path
from typing import Type

from PyQt5 import QtGui, QtWidgets

import ztrack.gui


def launch(
    Widget: Type[QtWidgets.QWidget],
    style: str = "light",
    show: str = None,
    modern_window=False,
    **kwargs,
) -> int:
    app = QtWidgets.QApplication(sys.argv)
    widget = Widget(**kwargs)
    icon_path = str(Path(ztrack.gui.__file__).parent / "img" / "logo.svg")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    try:
        import qtmodern.styles
        import qtmodern.windows

        if modern_window:
            widget = qtmodern.windows.ModernWindow(widget)
        getattr(qtmodern.styles, style)(app)
    except TypeError:
        pass
    except ModuleNotFoundError:
        app.setStyle(style)     # type: ignore
    except AttributeError:
        app.setStyle(style)     # type: ignore
    finally:
        if isinstance(show, str) and (show := show.capitalize()) in (
            "FullScreen",
            "Maximized",
            "Minimized",
            "Normal",
        ):
            getattr(widget, f"show{show}")()
        else:
            widget.show()

        return app.exec()
