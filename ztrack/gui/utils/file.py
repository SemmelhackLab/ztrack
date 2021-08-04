from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets

if TYPE_CHECKING:
    from typing import Iterable, List, Tuple


def selectFiles(filter_: str = None, native=False) -> List[str]:
    dialog = QtWidgets.QFileDialog()
    dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, not native)

    if filter_ is not None:
        dialog.setNameFilter(filter_)

    return dialog.selectedFiles() if dialog.exec() else []


def selectVideoPaths(
    extensions: Iterable[str] = (".avi", ".mp4"), native=False
):
    filter_ = f'Videos (*{" *".join(extensions)})'
    return selectFiles(filter_, native)


def selectVideoDirectories(
    options: Iterable[Tuple[str, bool]] = None
) -> Tuple[List[str], List[bool]]:
    dialog = QtWidgets.QFileDialog()
    dialog.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
    dialog.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
    dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
    dialog.setMinimumSize(1280, 960)

    checkBoxes: List[QtWidgets.QCheckBox] = []

    if options is not None:
        vBoxLayout = QtWidgets.QVBoxLayout()

        for description, checked in options:
            checkBox = QtWidgets.QCheckBox(dialog)
            checkBox.setText(description)
            checkBox.setChecked(checked)
            vBoxLayout.addWidget(checkBox)
            checkBoxes.append(checkBox)

        groupBox = QtWidgets.QGroupBox(dialog)
        groupBox.setTitle("Options")
        groupBox.setLayout(vBoxLayout)

        layout = dialog.layout()

        if isinstance(layout, QtWidgets.QGridLayout):
            layout.addWidget(groupBox, 4, 0, 1, 3)
        else:
            layout.addWidget(groupBox)

    fileView = dialog.findChild(QtWidgets.QListView, "listView")
    treeView = dialog.findChild(QtWidgets.QTreeView)

    for view in (fileView, treeView):
        if view is not None:
            view.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )

    return (dialog.selectedFiles() if dialog.exec() else []), [
        checkBox.isChecked() for checkBox in checkBoxes
    ]
