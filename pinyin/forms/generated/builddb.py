# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/builddb.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_BuildDB(object):
    def setupUi(self, BuildDB):
        BuildDB.setObjectName("BuildDB")
        BuildDB.resize(400, 260)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(BuildDB)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.explanationLabel = QtWidgets.QLabel(BuildDB)
        self.explanationLabel.setWordWrap(True)
        self.explanationLabel.setOpenExternalLinks(True)
        self.explanationLabel.setObjectName("explanationLabel")
        self.verticalLayout_2.addWidget(self.explanationLabel)
        self.progressBar = QtWidgets.QProgressBar(BuildDB)
        self.progressBar.setMaximum(0)
        self.progressBar.setProperty("value", -1)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout_2.addWidget(self.progressBar)
        self.cancelButtonBox = QtWidgets.QDialogButtonBox(BuildDB)
        self.cancelButtonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel)
        self.cancelButtonBox.setObjectName("cancelButtonBox")
        self.verticalLayout_2.addWidget(self.cancelButtonBox)

        self.retranslateUi(BuildDB)
        QtCore.QMetaObject.connectSlotsByName(BuildDB)

    def retranslateUi(self, BuildDB):
        _translate = QtCore.QCoreApplication.translate
        BuildDB.setWindowTitle(_translate("BuildDB", "Build Pinyin Toolkit Database"))

