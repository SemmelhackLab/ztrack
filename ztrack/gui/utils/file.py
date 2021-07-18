from typing import Iterable, List, Tuple

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView


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


def selectVideoDirectories() -> Tuple[List[str], bool, bool, bool]:
    dialog = QtWidgets.QFileDialog()
    dialog.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
    dialog.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
    dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
    dialog.setMinimumSize(1280, 960)

    recursiveCheckBox = QtWidgets.QCheckBox(dialog)
    recursiveCheckBox.setText("Include subdirectories")
    recursiveCheckBox.setChecked(True)
    sameConfigCheckBox = QtWidgets.QCheckBox(dialog)
    sameConfigCheckBox.setText("Use one configuration file per directory")
    sameConfigCheckBox.setChecked(True)
    overwriteCheckBox = QtWidgets.QCheckBox(dialog)
    overwriteCheckBox.setText("Overwrite existing configuration files")

    vBoxLayout = QtWidgets.QVBoxLayout()
    vBoxLayout.addWidget(recursiveCheckBox)
    vBoxLayout.addWidget(sameConfigCheckBox)
    vBoxLayout.addWidget(overwriteCheckBox)

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
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    return (
        (dialog.selectedFiles() if dialog.exec() else []),
        recursiveCheckBox.isChecked(),
        sameConfigCheckBox.isChecked(),
        overwriteCheckBox.isChecked(),
    )
