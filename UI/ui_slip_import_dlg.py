# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'slip_import_dlg.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_ImportSlipDlg(object):
    def setupUi(self, ImportSlipDlg):
        if not ImportSlipDlg.objectName():
            ImportSlipDlg.setObjectName(u"ImportSlipDlg")
        ImportSlipDlg.resize(517, 665)
        self.verticalLayout = QVBoxLayout(ImportSlipDlg)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.QRGroup = QGroupBox(ImportSlipDlg)
        self.QRGroup.setObjectName(u"QRGroup")
        self.horizontalLayout = QHBoxLayout(self.QRGroup)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.GetClipboardBtn = QPushButton(self.QRGroup)
        self.GetClipboardBtn.setObjectName(u"GetClipboardBtn")

        self.horizontalLayout.addWidget(self.GetClipboardBtn)

        self.LoadQRfromFileBtn = QPushButton(self.QRGroup)
        self.LoadQRfromFileBtn.setObjectName(u"LoadQRfromFileBtn")

        self.horizontalLayout.addWidget(self.LoadQRfromFileBtn)


        self.verticalLayout.addWidget(self.QRGroup)

        self.JSONGroup = QGroupBox(ImportSlipDlg)
        self.JSONGroup.setObjectName(u"JSONGroup")
        self.horizontalLayout_2 = QHBoxLayout(self.JSONGroup)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.LoadJSONfromFileBtn = QPushButton(self.JSONGroup)
        self.LoadJSONfromFileBtn.setObjectName(u"LoadJSONfromFileBtn")

        self.horizontalLayout_2.addWidget(self.LoadJSONfromFileBtn)


        self.verticalLayout.addWidget(self.JSONGroup)

        self.SlipDataGroup = QGroupBox(ImportSlipDlg)
        self.SlipDataGroup.setObjectName(u"SlipDataGroup")
        self.formLayout = QFormLayout(self.SlipDataGroup)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(2, 2, 2, 2)
        self.FD = QLineEdit(self.SlipDataGroup)
        self.FD.setObjectName(u"FD")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.FD)

        self.FN = QLineEdit(self.SlipDataGroup)
        self.FN.setObjectName(u"FN")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.FN)

        self.FP = QLineEdit(self.SlipDataGroup)
        self.FP.setObjectName(u"FP")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.FP)

        self.FNlbl = QLabel(self.SlipDataGroup)
        self.FNlbl.setObjectName(u"FNlbl")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.FNlbl)

        self.FPlbl = QLabel(self.SlipDataGroup)
        self.FPlbl.setObjectName(u"FPlbl")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.FPlbl)

        self.GetSlipBtn = QPushButton(self.SlipDataGroup)
        self.GetSlipBtn.setObjectName(u"GetSlipBtn")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.GetSlipBtn)

        self.FDlbl = QLabel(self.SlipDataGroup)
        self.FDlbl.setObjectName(u"FDlbl")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.FDlbl)

        self.DummyLbl = QLabel(self.SlipDataGroup)
        self.DummyLbl.setObjectName(u"DummyLbl")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.DummyLbl)

        self.TimestampLbl = QLabel(self.SlipDataGroup)
        self.TimestampLbl.setObjectName(u"TimestampLbl")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.TimestampLbl)

        self.AmountLbl = QLabel(self.SlipDataGroup)
        self.AmountLbl.setObjectName(u"AmountLbl")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.AmountLbl)

        self.SlipTimstamp = QDateTimeEdit(self.SlipDataGroup)
        self.SlipTimstamp.setObjectName(u"SlipTimstamp")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.SlipTimstamp)

        self.SlipAmount = QLineEdit(self.SlipDataGroup)
        self.SlipAmount.setObjectName(u"SlipAmount")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.SlipAmount)

        self.SlipTypeLbl = QLabel(self.SlipDataGroup)
        self.SlipTypeLbl.setObjectName(u"SlipTypeLbl")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.SlipTypeLbl)

        self.SlipType = QLineEdit(self.SlipDataGroup)
        self.SlipType.setObjectName(u"SlipType")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.SlipType)


        self.verticalLayout.addWidget(self.SlipDataGroup)

        self.SlipGroup = QGroupBox(ImportSlipDlg)
        self.SlipGroup.setObjectName(u"SlipGroup")
        self.gridLayout = QGridLayout(self.SlipGroup)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.lineEdit_4 = QLineEdit(self.SlipGroup)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.gridLayout.addWidget(self.lineEdit_4, 1, 1, 1, 1)

        self.lineEdit_5 = QLineEdit(self.SlipGroup)
        self.lineEdit_5.setObjectName(u"lineEdit_5")

        self.gridLayout.addWidget(self.lineEdit_5, 1, 2, 1, 1)

        self.PeerLbl = QLabel(self.SlipGroup)
        self.PeerLbl.setObjectName(u"PeerLbl")

        self.gridLayout.addWidget(self.PeerLbl, 1, 0, 1, 1)

        self.tableView = QTableView(self.SlipGroup)
        self.tableView.setObjectName(u"tableView")

        self.gridLayout.addWidget(self.tableView, 2, 1, 1, 2)

        self.LinesLbl = QLabel(self.SlipGroup)
        self.LinesLbl.setObjectName(u"LinesLbl")
        self.LinesLbl.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.LinesLbl, 2, 0, 1, 1)

        self.LoadedLbl = QLabel(self.SlipGroup)
        self.LoadedLbl.setObjectName(u"LoadedLbl")

        self.gridLayout.addWidget(self.LoadedLbl, 0, 1, 1, 1)

        self.StoredLbl = QLabel(self.SlipGroup)
        self.StoredLbl.setObjectName(u"StoredLbl")

        self.gridLayout.addWidget(self.StoredLbl, 0, 2, 1, 1)


        self.verticalLayout.addWidget(self.SlipGroup)

        self.frame = QFrame(ImportSlipDlg)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(2, 2, 2, 2)
        self.ClearBtn = QPushButton(self.frame)
        self.ClearBtn.setObjectName(u"ClearBtn")

        self.horizontalLayout_4.addWidget(self.ClearBtn)

        self.AddOperationBtn = QPushButton(self.frame)
        self.AddOperationBtn.setObjectName(u"AddOperationBtn")

        self.horizontalLayout_4.addWidget(self.AddOperationBtn)

        self.CloseBtn = QPushButton(self.frame)
        self.CloseBtn.setObjectName(u"CloseBtn")

        self.horizontalLayout_4.addWidget(self.CloseBtn)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(ImportSlipDlg)

        QMetaObject.connectSlotsByName(ImportSlipDlg)
    # setupUi

    def retranslateUi(self, ImportSlipDlg):
        ImportSlipDlg.setWindowTitle(QCoreApplication.translate("ImportSlipDlg", u"Import Slip", None))
        self.QRGroup.setTitle(QCoreApplication.translate("ImportSlipDlg", u"From QR-code", None))
        self.GetClipboardBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Get from clipboard", None))
        self.LoadQRfromFileBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Load from file", None))
        self.JSONGroup.setTitle(QCoreApplication.translate("ImportSlipDlg", u"From JSON-file", None))
        self.LoadJSONfromFileBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Load from file", None))
        self.SlipDataGroup.setTitle(QCoreApplication.translate("ImportSlipDlg", u"From slip data", None))
        self.FNlbl.setText(QCoreApplication.translate("ImportSlipDlg", u"FN:", None))
        self.FPlbl.setText(QCoreApplication.translate("ImportSlipDlg", u"FP:", None))
        self.GetSlipBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Get Slip", None))
        self.FDlbl.setText(QCoreApplication.translate("ImportSlipDlg", u"FD:", None))
        self.DummyLbl.setText("")
        self.TimestampLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Date/Time:", None))
        self.AmountLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Amount:", None))
        self.SlipTimstamp.setDisplayFormat(QCoreApplication.translate("ImportSlipDlg", u"dd/MM/yyyy hh:mm:ss", None))
        self.SlipTypeLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Type:", None))
        self.SlipGroup.setTitle(QCoreApplication.translate("ImportSlipDlg", u"Slip", None))
        self.PeerLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Peer:", None))
        self.LinesLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Lines:", None))
        self.LoadedLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"Imported:", None))
        self.StoredLbl.setText(QCoreApplication.translate("ImportSlipDlg", u"To be added:", None))
        self.ClearBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Clear", None))
        self.AddOperationBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Add", None))
        self.CloseBtn.setText(QCoreApplication.translate("ImportSlipDlg", u"Close", None))
    # retranslateUi
