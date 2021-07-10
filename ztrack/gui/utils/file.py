from PyQt5 import QtCore, QtWidgets


def selectFiles(filter_=None, native=False):
    dialog = QtWidgets.QFileDialog()

    dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, not native)

    if isinstance(filter_, str):
        dialog.setNameFilter(filter_)

    if dialog.exec():
        return dialog.selectedFiles()

    return []


def selectVideoPaths(extensions=(".avi", ".mp4"), native=False):
    filter_ = f'Videos (*{" *".join(extensions)})'
    return selectFiles(filter_, native)


def selectVideoDirectories():
    dialog = QtWidgets.QFileDialog()
    dialog.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
    dialog.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
    dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)

    recursiveCheckBox = QtWidgets.QCheckBox(dialog)
    recursiveCheckBox.setText("Include subdirectories")

    sameConfigCheckBox = QtWidgets.QCheckBox(dialog)
    sameConfigCheckBox.setText(
        "Generate one configuration file for each " "directory"
    )

    overwriteCheckBOx = QtWidgets.QCheckBox(dialog)
    overwriteCheckBOx.setText("Overwrite existing configuration files")

    recursiveCheckBox.setChecked(True)
    sameConfigCheckBox.setChecked(True)

    vBoxLayout = QtWidgets.QVBoxLayout()
    vBoxLayout.addWidget(recursiveCheckBox)
    vBoxLayout.addWidget(sameConfigCheckBox)
    vBoxLayout.addWidget(overwriteCheckBOx)

    groupBox = QtWidgets.QGroupBox(dialog)
    groupBox.setTitle("Options")
    groupBox.setLayout(vBoxLayout)

    if isinstance(dialog.layout(), QtWidgets.QGridLayout):
        dialog.layout().addWidget(groupBox, 4, 0, 1, 3)
    else:
        dialog.layout().addWidget(groupBox)

    if fileView := dialog.findChild(QtWidgets.QListView, "listView"):
        fileView.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

    if treeView := dialog.findChild(QtWidgets.QTreeView):
        treeView.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

    dialog.setMinimumSize(1280, 960)

    return (
        (dialog.selectedFiles() if dialog.exec() else []),
        recursiveCheckBox.isChecked(),
        sameConfigCheckBox.isChecked(),
        overwriteCheckBOx.isChecked(),
    )
