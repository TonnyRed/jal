from functools import partial
from datetime import datetime, timezone
import logging

from jal.constants import TransactionType, CorporateAction
from jal.reports.helpers import XLSX
from jal.reports.dlsg import DLSG
from jal.ui_custom.helpers import g_tr
from jal.db.helpers import executeSQL, readSQLrecord, readSQL
from PySide2.QtWidgets import QDialog, QFileDialog
from PySide2.QtCore import Property, Slot
from jal.ui.ui_tax_export_dlg import Ui_TaxExportDlg


# -----------------------------------------------------------------------------------------------------------------------
class TaxExportDialog(QDialog, Ui_TaxExportDlg):
    def __init__(self, parent, db):
        QDialog.__init__(self)
        self.setupUi(self)

        self.AccountWidget.init_db(db)
        self.XlsSelectBtn.pressed.connect(partial(self.OnFileBtn, 'XLS-OUT'))
        self.InitialSelectBtn.pressed.connect(partial(self.OnFileBtn, 'DLSG-IN'))
        self.OutputSelectBtn.pressed.connect(partial(self.OnFileBtn, 'DLSG-OUT'))

        # center dialog with respect to parent window
        x = parent.x() + parent.width() / 2 - self.width() / 2
        y = parent.y() + parent.height() / 2 - self.height() / 2
        self.setGeometry(x, y, self.width(), self.height())

    @Slot()
    def OnFileBtn(self, type):
        selector = {
            'XLS-OUT': (g_tr('TaxExportDialog', "Save tax reports to:"),
                        g_tr('TaxExportDialog', "Excel files (*.xlsx)"),
                        '.xlsx', self.XlsFileName),
            'DLSG-IN': (g_tr('TaxExportDialog', "Get tax form template from:"),
                        g_tr('TaxExportDialog', "Tax form 2020 (*.dc0)"),
                        '.dc0', self.DlsgInFileName),
            'DLSG-OUT': (g_tr('TaxExportDialog', "Save tax form to:"),
                         g_tr('TaxExportDialog', "Tax form 2020 (*.dc0)"),
                         '.dc0', self.DlsgOutFileName),
        }
        if type[-3:] == '-IN':
            filename = QFileDialog.getOpenFileName(self, selector[type][0], ".", selector[type][1])
        elif type[-4:] == '-OUT':
            filename = QFileDialog.getSaveFileName(self, selector[type][0], ".", selector[type][1])
        else:
            raise ValueError
        if filename[0]:
            if filename[1] == selector[type][1] and filename[0][-len(selector[type][2]):] != selector[type][2]:
                selector[type][3].setText(filename[0] + selector[type][2])
            else:
                selector[type][3].setText(filename[0])

    def getYear(self):
        return self.Year.value()

    def getXlsFilename(self):
        return self.XlsFileName.text()

    def getAccount(self):
        return self.AccountWidget.selected_id

    def getDlsgState(self):
        return self.DlsgGroup.isChecked()

    def getDslgInFilename(self):
        return self.DlsgInFileName.text()

    def getDslgOutFilename(self):
        return self.DlsgOutFileName.text()

    def getDividendsOnly(self):
        return self.DividendsOnly.isChecked()

    def getNoSettlement(self):
        return self.NoSettlement.isChecked()

    year = Property(int, fget=getYear)
    xls_filename = Property(str, fget=getXlsFilename)
    account = Property(int, fget=getAccount)
    update_dlsg = Property(bool, fget=getDlsgState)
    dlsg_in_filename = Property(str, fget=getDslgInFilename)
    dlsg_out_filename = Property(str, fget=getDslgOutFilename)
    dlsg_dividends_only = Property(bool, fget=getDividendsOnly)
    no_settelement = Property(bool, fget=getNoSettlement)


# -----------------------------------------------------------------------------------------------------------------------
class TaxesRus:
    RPT_METHOD = 0
    RPT_TITLE = 1
    RPT_COLUMNS = 2
    RPT_DATA_ROWS = 3

    COL_TITLE = 0
    COL_WIDTH = 1
    COL_FIELD = 2
    COL_DESCR = -1

    CorpActionText = {
        CorporateAction.SymbolChange: "Смена символа {before} {old} -> {after} {new}",
        CorporateAction.Split: "Сплит {old} {before} в {after}",
        CorporateAction.SpinOff: "Выделение компании {after} {new} из {before} {old}",
        CorporateAction.Merger: "Слияние компании, конвертация {before} {old} в {after} {new}",
        CorporateAction.StockDividend: "Допэмиссия акций: {after} {new}"
    }

    def __init__(self, db):
        self.db = db
        self.account_id = 0
        self.year_begin = 0
        self.year_end = 0
        self.account_currency = ''
        self.broker_name = ''
        self.use_settlement = True
        self.current_report = None
        self.data_start_row = 9
        self.reports_xls = None
        self.statement = None
        self.current_sheet = None
        self.reports = {
            "Дивиденды": (self.prepare_dividends,
                          "Отчет по дивидендам, полученным в отчетном периоде",
                          {
                              0: ("Дата выплаты", 10, ("payment_date", "date"), "Дата, в которую дивиденд был зачислен на счет согласно отчету брокера"),
                              1: ("Ценная бумага", 8, ("symbol", "text"), "Краткое наименование ценной бумаги"),
                              2: ("Полное наименование", 50, ("full_name", "text"), "Полное наименование ценной бумаги"),
                              3: ("Курс {currency}/RUB на дату выплаты", 16, ("rate", "number", 4), "Официальный курс валюты выплаты, установленный ЦБ РФ на дату выплаты дивиденда"),
                              4: ("Доход, {currency}", 12, ("amount", "number", 2), "Сумма выплаченного дивиденда в валюте счета"),
                              5: ("Доход, RUB (код 1010)", 12, ("amount_rub", "number", 2), "Сумма выплаченного дивиденда в рублях по курсу ЦБ РФ на дату выплаты (= Столбец 4 x Столбец 5)"),
                              6: ("Налог упл., {currency}", 12, ("tax", "number", 2), "Сумма налога, удержанная эмитентом, в валюте счета"),
                              7: ("Налог упл., RUB", 12, ("tax_rub", "number", 2), "Сумма налога, удержанная эмитентом, в рублях по курсу ЦБ РФ на дату удержания (= Столбец 4 x Столбец 7)"),
                              8: ("Налог к уплате, RUB", 12, ("tax2pay", "number", 2), "Сумма налога, подлежащая уплате в РФ (= 13% от Столбца 6 - Столбец 8)"),
                              9: ("Страна", 20, ("country", "text"), "Страна регистрации эмитента ценной бумаги "),
                              10: ("СОИДН", 7, ("tax_treaty", "bool", ("Нет", "Да")), "Наличие у Российской Федерации договора об избежании двойного налогообложения со страной эмитента")
                          }
                          ),
            "Сделки с ЦБ": (self.prepare_trades,
                            "Отчет по сделкам с ценными бумагами, завершённым в отчетном периоде",
                            {
                                0: ("Ценная бумага", 8, ("symbol", "text", 0, 0, 1), None, "Краткое наименование ценной бумаги"),
                                1: ("Кол-во", 8, ("qty", "number", 0, 0, 1), None, "Количество ЦБ в сделке"),
                                2: ("Тип сделки", 8, ("o_type", "text"), ("c_type", "text"), "Направление сделки (полкупка или продажа)"),
                                3: ("Дата сделки", 10, ("o_date", "date"), ("c_date", "date"), "Дата заключения сделки (и уплаты комиссии из столбца 11)"),
                                4: ("Курс {currency}/RUB на дату сделки", 9, ("o_rate", "number", 4), ("c_rate", "number", 4), "Официальный курс валюты,  установленный ЦБ РФ на дату заключения сделки"),
                                5: ("Дата поставки", 10, ("os_date", "date"), ("cs_date", "date"), "Дата рачетов по сделке / Дата поставки ценных бумаг"),
                                6: ("Курс {currency}/RUB на дату поставки", 9, ("os_rate", "number", 4), ("cs_rate", "number", 4), "Официальный курс валюты,  установленный ЦБ РФ на дату поставки / расчетов по сделке"),
                                7: ("Цена, {currency}", 12, ("o_price", "number", 6), ("c_price", "number", 6), "Цена одной ценной бумаги в валюте счета"),
                                8: ("Сумма сделки, {currency}", 12, ("o_amount", "number", 2), ("c_amount", "number", 2), "Сумма сделки в валюте счета (= Столбец 2 * Столбец 8)"),
                                9: ("Сумма сделки, RUB", 12, ("o_amount_rub", "number", 2), ("c_amount_rub", "number", 2), "Сумма сделки в рублях (= Столбец 9 * Столбец 7)"),
                                10: ("Комиссия, {currency}", 12, ("o_fee", "number", 6), ("c_fee", "number", 6), "Комиссия брокера за совершение сделки в валюте счета"),
                                11: ("Комиссия, RUB", 9, ("o_fee_rub", "number", 2), ("c_fee_rub", "number", 2), "Комиссия брокера за совершение сделки в рублях ( = Столбец 11 * Столбец 5)"),
                                12: ("Доход, RUB (код 1530)", 12, ("income_rub", "number", 2, 0, 1), None, "Доход, полученных от продажи ценных бумаг (равен сумме сделки продажи из столбца 10)"),
                                13: ("Расход, RUB (код 201)", 12, ("spending_rub", "number", 2, 0, 1), None, "Расход, понесённый на покупку ценных бумаг и уплату комиссий (равен сумме стелки покупки из столбца 10 + комиссии из столбца 12)"),
                                14: ("Финансовый результат, RUB", 12, ("profit_rub", "number", 2, 0, 1), None, "Финансовый результат сделки в рублях (= Столбец 13 - Столбец 14)"),
                                15: ("Финансовый результат, {currency}", 12, ("profit", "number", 2, 0, 1), None, "Финансовый результат сделки в валюте счета")
                            }
                            ),
            "Сделки с ПФИ": (self.prepare_derivatives,
                             "Отчет по сделкам с производными финансовыми инструментами, завершённым в отчетном периоде",
                             {
                                 0: ("Ценная бумага", 8, ("symbol", "text", 0, 0, 1), None, "Краткое наименование контракта"),
                                 1: ("Кол-во", 8, ("qty", "number", 0, 0, 1), None, "Количество ЦБ в сделке"),
                                 2: ("Тип сделки", 8, ("o_type", "text"), ("c_type", "text"), "Направление сделки (полкупка или продажа)"),
                                 3: ("Дата сделки", 10, ("o_date", "date"), ("c_date", "date"), "Дата заключения сделки (и уплаты комиссии из столбца 11)"),
                                 4: ("Курс {currency}/RUB на дату сделки", 9, ("o_rate", "number", 4), ("c_rate", "number", 4), "Официальный курс валюты,  установленный ЦБ РФ на дату заключения сделки"),
                                 5: ("Дата поставки", 10, ("os_date", "date"), ("cs_date", "date"), "Дата рачетов по сделке / Дата поставки ценных бумаг"),
                                 6: ("Курс {currency}/RUB на дату поставки", 9, ("os_rate", "number", 4), ("cs_rate", "number", 4), "Официальный курс валюты,  установленный ЦБ РФ на дату поставки / расчетов по сделке"),
                                 7: ("Цена, {currency}", 12, ("o_price", "number", 6), ("c_price", "number", 6), "Цена одной ценной бумаги в валюте счета"),
                                 8: ("Сумма сделки, {currency}", 12, ("o_amount", "number", 2), ("c_amount", "number", 2), "Сумма сделки в валюте счета (= Столбец 2 * Столбец 8)"),
                                 9: ("Сумма сделки, RUB", 12, ("o_amount_rub", "number", 2), ("c_amount_rub", "number", 2), "Сумма сделки в рублях (= Столбец 9 * Столбец 7)"),
                                 10: ("Комиссия, {currency}", 12, ("o_fee", "number", 6), ("c_fee", "number", 6), "Комиссия брокера за совершение сделки в валюте счета"),
                                 11: ("Комиссия, RUB", 9, ("o_fee_rub", "number", 2), ("c_fee_rub", "number", 2), "Комиссия брокера за совершение сделки в рублях ( = Столбец 11 * Столбец 5)"),
                                 12: ("Доход, RUB (код 1532)", 12, ("income_rub", "number", 2, 0, 1), None, "Доход, полученных от продажи ценных бумаг (равен сумме сделки продажи из столбца 10)"),
                                 13: ("Расход, RUB (код 206)", 12, ("spending_rub", "number", 2, 0, 1), None, "Расход, понесённый на покупку ценных бумаг и уплату комиссий (равен сумме стелки покупки из столбца 10 + комиссии из столбца 12)"),
                                 14: ("Финансовый результат, RUB", 12, ("profit_rub", "number", 2, 0, 1), None, "Финансовый результат сделки в рублях (= Столбец 13 - Столбец 14)"),
                                 15: ("Финансовый результат, {currency}", 12, ("profit", "number", 2, 0, 1), None, "Финансовый результат сделки в валюте счета")
                             }
                             ),
            "Комиссии, Платежи": (self.prepare_broker_fees,
                                 "Отчет по комиссиям и прочим платежам в отчетном периоде",
                                 {
                                     0: ("Описание", 50, ("note", "text"), "Описание платежа"),
                                     1: ("Сумма, {currency}", 8, ("amount", "number", 2), "Сумма платежа в валюте счёта"),
                                     2: ("Дата оплаты", 10, ("payment_date", "date"), "Дата платежа"),
                                     3: ("Курс {currency}/RUB на дату оплаты", 10, ("rate", "number", 4), "Официальный курс валюты,  установленный ЦБ РФ на дату платежа"),
                                     4: ("Сумма, RUB", 10, ("amount_rub", "number", 2), "Сумма платежа в рублях (= Столбец 2 * Столбец 4)")
                                 }
                                 ),
            "Корп.события": (self.prepare_corporate_actions,
                             "Отчет по сделкам с ценными бумагами, завершённым в отчетном периоде "
                             "с предшествовавшими корпоративными событиями",
                             {
                                 0: ("Операция", 20, ("operation", "text"), ("operation", "text"), "Описание операции"),
                                 1: ("Дата операции", 10, ("t_date", "date"), ("a_date", "date"), "Дата совершения операции (и уплаты комиссии из столбца 11)"),
                                 2: ("Ценная бумага", 8, ("symbol", "text"), ("description", "text", 0, 9, 0), "Краткое наименование ценной бумаги"),
                                 3: ("Кол-во", 8, ("qty", "number", 4), None, "Количество ЦБ в сделке"),
                                 4: ("Курс {currency}/RUB на дату сделки", 9, ("t_rate", "number", 4), None, "Официальный курс валюты,  установленный ЦБ РФ на дату операции"),
                                 5: ("Дата поставки", 10, ("s_date", "date"), None, "Дата рачетов по сделке / Дата поставки ценных бумаг"),
                                 6: ("Курс {currency}/RUB на дату поставки", 9, ("s_rate", "number", 4), None, "Официальный курс валюты,  установленный ЦБ РФ на дату расчетов по операции"),
                                 7: ("Цена, {currency}", 12, ("price", "number", 6), None, "Цена одной ценной бумаги в валюте счета"),
                                 8: ("Сумма сделки, {currency}", 12, ("amount", "number", 2), None, "Сумма сделки в валюте счета (= Столбец 2 * Столбец 8)"),
                                 9: ("Сумма сделки, RUB", 12, ("amount_rub", "number", 2), None, "Сумма сделки в рублях (= Столбец 9 * Столбец 7)"),
                                 10: ("Комиссия, {currency}", 12, ("fee", "number", 6), None, "Комиссия брокера за совершение сделки в валюте счета"),
                                 11: ("Комиссия, RUB", 9, ("fee_rub", "number", 2), None, "Комиссия брокера за совершение сделки в рублях ( = Столбец 11 * Столбец 5)")
                             }
                             )
        }

    def showTaxesDialog(self, parent):
        dialog = TaxExportDialog(parent, self.db)
        if dialog.exec_():
            self.use_settlement = not dialog.no_settelement
            self.save2file(dialog.xls_filename, dialog.year, dialog.account, dlsg_update=dialog.update_dlsg,
                           dlsg_in=dialog.dlsg_in_filename, dlsg_out=dialog.dlsg_out_filename,
                           dlsg_dividends_only=dialog.dlsg_dividends_only)

    def save2file(self, taxes_file, year, account_id,
                  dlsg_update=False, dlsg_in=None, dlsg_out=None, dlsg_dividends_only=False):
        self.account_id = account_id
        self.account_number, self.account_currency = \
            readSQL(self.db,
                    "SELECT a.number, c.name FROM accounts AS a "
                    "LEFT JOIN assets AS c ON a.currency_id = c.id WHERE a.id=:account",
                    [(":account", account_id)])
        self.broker_name = readSQL(self.db,
                                   "SELECT b.name FROM accounts AS a "
                                   "LEFT JOIN agents AS b ON a.organization_id = b.id WHERE a.id=:account",
                                   [(":account", account_id)])
        self.year_begin = int(datetime.strptime(f"{year}", "%Y").replace(tzinfo=timezone.utc).timestamp())
        self.year_end = int(datetime.strptime(f"{year + 1}", "%Y").replace(tzinfo=timezone.utc).timestamp())

        self.reports_xls = XLSX(taxes_file)

        self.statement = None
        if dlsg_update:
            self.statement = DLSG(only_dividends=dlsg_dividends_only)
            try:
                self.statement.read_file(dlsg_in)
            except:
                logging.error(g_tr('TaxesRus', "Can't open tax form file ") + f"'{dlsg_in}'")
                return

        self.prepare_exchange_rate_dates()
        for report in self.reports:
            self.current_report = report
            self.current_sheet = self.reports_xls.add_report_sheet(report)
            self.add_report_header()
            report_description = self.reports[self.current_report]
            next_row = report_description[self.RPT_METHOD]()
            self.add_report_footer(next_row)

        self.reports_xls.save()

        if dlsg_update:
            try:
                self.statement.write_file(dlsg_out)
            except:
                logging.error(g_tr('TaxesRus', "Can't write tax form into file ") + f"'{dlsg_out}'")

    # This method puts header on each report sheet
    def add_report_header(self):
        report = self.reports[self.current_report]
        self.current_sheet.write(0, 0, report[self.RPT_TITLE], self.reports_xls.formats.Bold())
        self.current_sheet.write(2, 0, "Документ-основание:", self.reports_xls.formats.CommentText())
        self.current_sheet.write(3, 0, f"Период: {datetime.utcfromtimestamp(self.year_begin).strftime('%d.%m.%Y')}"
                                       f" - {datetime.utcfromtimestamp(self.year_end - 1).strftime('%d.%m.%Y')}",
                                 self.reports_xls.formats.CommentText())
        self.current_sheet.write(4, 0, "ФИО:", self.reports_xls.formats.CommentText())
        self.current_sheet.write(5, 0, f"Номер счета: {self.account_number} ({self.account_currency})",
                                 self.reports_xls.formats.CommentText())

        header_row = {}
        numbers_row = {}  # Put column numbers for reference
        for column in report[self.RPT_COLUMNS]:
            # make tuple for each column i: ("Column_Title", xlsx.formats.ColumnHeader(), Column_Width, 0, 0)
            title = report[self.RPT_COLUMNS][column][self.COL_TITLE].format(currency=self.account_currency)
            width = report[self.RPT_COLUMNS][column][self.COL_WIDTH]
            header_row[column] = (title, self.reports_xls.formats.ColumnHeader(), width, 0, 0)
            numbers_row[column] = (f"({column + 1})", self.reports_xls.formats.ColumnHeader())
        self.reports_xls.write_row(self.current_sheet, 7, header_row, 60)
        self.reports_xls.write_row(self.current_sheet, 8, numbers_row)

    def add_report_row(self, row, data, even_odd=1, alternative=0):
        KEY_NAME = 0
        VALUE_FMT = 1
        FMT_DETAILS = 2
        H_SPAN = 3
        V_SPAN = 4

        report = self.reports[self.current_report]
        data_row = {}
        idx = self.COL_FIELD + alternative
        for column in report[self.RPT_COLUMNS]:
            field_dscr = report[self.RPT_COLUMNS][column][idx]
            if field_dscr is not None:
                value = data[field_dscr[KEY_NAME]]
                format_as = field_dscr[VALUE_FMT]
                if format_as == "text":
                    fmt = self.reports_xls.formats.Text(even_odd)
                elif format_as == "number":
                    precision = field_dscr[FMT_DETAILS]
                    fmt = self.reports_xls.formats.Number(even_odd, tolerance=precision)
                elif format_as == "date":
                    value = datetime.utcfromtimestamp(value).strftime('%d.%m.%Y')
                    fmt = self.reports_xls.formats.Text(even_odd)
                elif format_as == "bool":
                    value = field_dscr[FMT_DETAILS][value]
                    fmt = self.reports_xls.formats.Text(even_odd)
                else:
                    raise ValueError
                if len(field_dscr) == 5:  # There are horizontal or vertical span defined
                    data_row[column] = (value, fmt, 0, field_dscr[H_SPAN], field_dscr[V_SPAN])
                else:
                    data_row[column] = (value, fmt)
        self.reports_xls.write_row(self.current_sheet, row, data_row)

    def add_report_footer(self, row):
        row += 1 # Skip one row from previous table
        self.current_sheet.write(row, 0, "Описание данных в стобцах таблицы",
                                 self.reports_xls.formats.CommentText())
        row += 1
        self.current_sheet.write(row, 0, "Номер столбца", self.reports_xls.formats.CommentText())
        self.current_sheet.write(row, 2, "Описание", self.reports_xls.formats.CommentText())
        report = self.reports[self.current_report]
        for column in report[self.RPT_COLUMNS]:
            row += 1
            self.current_sheet.write(row, 0, column + 1, self.reports_xls.formats.CommentText())
            self.current_sheet.write(row, 2, report[self.RPT_COLUMNS][column][self.COL_DESCR],
                                     self.reports_xls.formats.CommentText())

    # Exchange rates are present in database not for every date (and not every possible timestamp)
    # As any action has exact timestamp it won't match rough timestamp of exchange rate most probably
    # Function fills 't_last_dates' table with correspondence between 'real' timestamp and nearest 'exchange' timestamp
    def prepare_exchange_rate_dates(self):
        _ = executeSQL(self.db, "DELETE FROM t_last_dates")
        _ = executeSQL(self.db,
                       "INSERT INTO t_last_dates(ref_id, timestamp) "
                       "SELECT ref_id, coalesce(MAX(q.timestamp), 0) AS timestamp "
                       "FROM (SELECT d.timestamp AS ref_id "
                       "FROM dividends AS d "
                       "WHERE d.account_id = :account_id "
                       "UNION "
                       "SELECT a.timestamp AS ref_id "
                       "FROM actions AS a "
                       "WHERE a.account_id = :account_id "
                       "UNION "
                       "SELECT t.timestamp AS ref_id "
                       "FROM deals AS d "
                       "LEFT JOIN sequence AS s ON (s.id=d.open_sid OR s.id=d.close_sid) AND s.type = 3 "
                       "LEFT JOIN trades AS t ON s.operation_id=t.id "
                       "WHERE d.account_id = :account_id "
                       "UNION "
                       "SELECT c.settlement AS ref_id "
                       "FROM deals AS d "
                       "LEFT JOIN sequence AS s ON (s.id=d.open_sid OR s.id=d.close_sid) AND s.type = 3 "
                       "LEFT JOIN trades AS c ON s.operation_id=c.id "
                       "WHERE d.account_id = :account_id "
                       "UNION "
                       "SELECT o.timestamp AS ref_id "
                       "FROM deals AS d "
                       "LEFT JOIN sequence AS s ON (s.id=d.open_sid OR s.id=d.close_sid) AND s.type = 5 "
                       "LEFT JOIN corp_actions AS o ON s.operation_id=o.id "
                       "WHERE d.account_id = :account_id) "
                       "LEFT JOIN accounts AS a ON a.id = :account_id "
                       "LEFT JOIN quotes AS q ON ref_id >= q.timestamp AND a.currency_id=q.asset_id "
                       "WHERE ref_id IS NOT NULL "
                       "GROUP BY ref_id", [(":account_id", self.account_id)])
        self.db.commit()

    # -----------------------------------------------------------------------------------------------------------------------
    def prepare_dividends(self):
        query = executeSQL(self.db,
                           "SELECT d.timestamp AS payment_date, s.name AS symbol, s.full_name AS full_name, "
                           "d.sum AS amount, d.sum_tax AS tax, q.quote AS rate , "
                           "c.name AS country, c.code AS country_code, c.tax_treaty AS tax_treaty "
                           "FROM dividends AS d "
                           "LEFT JOIN assets AS s ON s.id = d.asset_id "
                           "LEFT JOIN accounts AS a ON d.account_id = a.id "
                           "LEFT JOIN countries AS c ON d.tax_country_id = c.id "
                           "LEFT JOIN t_last_dates AS ld ON d.timestamp=ld.ref_id "
                           "LEFT JOIN quotes AS q ON ld.timestamp=q.timestamp AND a.currency_id=q.asset_id "
                           "WHERE d.timestamp>=:begin AND d.timestamp<:end AND d.account_id=:account_id "
                           "ORDER BY d.timestamp",
                           [(":begin", self.year_begin), (":end", self.year_end), (":account_id", self.account_id)])
        row = start_row = self.data_start_row
        while query.next():
            dividend = readSQLrecord(query, named=True)
            dividend["amount_rub"] = round(dividend["amount"] * dividend["rate"], 2) if dividend["rate"] else 0
            dividend["tax_rub"] = round(dividend["tax"] * dividend["rate"], 2) if dividend["rate"] else 0
            dividend["tax2pay"] = round(0.13 * dividend["amount_rub"], 2)
            if dividend["tax_treaty"]:
                if dividend["tax2pay"] > dividend["tax_rub"]:
                    dividend["tax2pay"] = dividend["tax2pay"] - dividend["tax_rub"]
                else:
                    dividend["tax2pay"] = 0
            self.add_report_row(row, dividend, even_odd=row)

            dividend["country_code"] = 'us' if dividend["country_code"] == 'xx' else dividend[
                "country_code"]  # TODO select right country code if it is absent
            if self.statement is not None:
                self.statement.add_dividend(dividend["country_code"], f"{dividend['symbol']} ({dividend['full_name']})",
                                            dividend['payment_date'], self.account_currency, dividend['amount'],
                                            dividend['amount_rub'], dividend['tax'], dividend['tax_rub'],
                                            dividend['rate'])
            row += 1

        self.reports_xls.add_totals_footer(self.current_sheet, start_row, row, [3, 4, 5, 6, 7, 8])
        return row+1

    # -----------------------------------------------------------------------------------------------------------------------
    def prepare_trades(self):
        # Take all actions without conversion
        query = executeSQL(self.db,
                           "SELECT s.name AS symbol, d.qty AS qty, "
                           "o.timestamp AS o_date, qo.quote AS o_rate, o.settlement AS os_date, "
                           "qos.quote AS os_rate, o.price AS o_price, o.qty AS o_qty, o.fee AS o_fee, "
                           "c.timestamp AS c_date, qc.quote AS c_rate, c.settlement AS cs_date, "
                           "qcs.quote AS cs_rate, c.price AS c_price, c.qty AS c_qty, c.fee AS c_fee "
                           "FROM deals AS d "
                           "JOIN sequence AS os ON os.id=d.open_sid AND os.type = 3 "
                           "LEFT JOIN trades AS o ON os.operation_id=o.id "
                           "JOIN sequence AS cs ON cs.id=d.close_sid AND cs.type = 3 "
                           "LEFT JOIN trades AS c ON cs.operation_id=c.id "
                           "LEFT JOIN assets AS s ON o.asset_id=s.id "
                           "LEFT JOIN accounts AS a ON a.id = :account_id "
                           "LEFT JOIN t_last_dates AS ldo ON o.timestamp=ldo.ref_id "
                           "LEFT JOIN quotes AS qo ON ldo.timestamp=qo.timestamp AND a.currency_id=qo.asset_id "
                           "LEFT JOIN t_last_dates AS ldos ON o.settlement=ldos.ref_id "
                           "LEFT JOIN quotes AS qos ON ldos.timestamp=qos.timestamp AND a.currency_id=qos.asset_id "
                           "LEFT JOIN t_last_dates AS ldc ON c.timestamp=ldc.ref_id "
                           "LEFT JOIN quotes AS qc ON ldc.timestamp=qc.timestamp AND a.currency_id=qc.asset_id "
                           "LEFT JOIN t_last_dates AS ldcs ON c.settlement=ldcs.ref_id "
                           "LEFT JOIN quotes AS qcs ON ldcs.timestamp=qcs.timestamp AND a.currency_id=qcs.asset_id "
                           "WHERE c.timestamp>=:begin AND c.timestamp<:end AND d.account_id=:account_id "
                           "AND s.type_id >= 2 AND s.type_id <= 4 "  # To select only stocks/bonds/ETFs
                           "ORDER BY o.timestamp, c.timestamp",
                           [(":begin", self.year_begin), (":end", self.year_end), (":account_id", self.account_id)])
        start_row = self.data_start_row
        data_row = 0
        while query.next():
            deal = readSQLrecord(query, named=True)
            row = start_row + (data_row * 2)
            if not self.use_settlement:
                deal['os_rate'] = deal['o_rate']
                deal['cs_rate'] = deal['c_rate']
            deal['o_type'] = "Покупка" if deal['qty'] >= 0 else "Продажа"
            deal['c_type'] = "Продажа" if deal['qty'] >= 0 else "Покупка"
            deal['o_amount'] = round(deal['o_price'] * abs(deal['qty']), 2)
            deal['o_amount_rub'] = round(deal['o_amount'] * deal['os_rate'], 2) if deal['os_rate'] else 0
            deal['c_amount'] = round(deal['c_price'] * abs(deal['qty']), 2)
            deal['c_amount_rub'] = round(deal['c_amount'] * deal['cs_rate'], 2) if deal['cs_rate'] else 0
            deal['o_fee'] = deal['o_fee'] * abs(deal['qty'] / deal['o_qty'])
            deal['c_fee'] = deal['c_fee'] * abs(deal['qty'] / deal['c_qty'])
            deal['o_fee_rub'] = round(deal['o_fee'] * deal['o_rate'], 2) if deal['o_rate'] else 0
            deal['c_fee_rub'] = round(deal['c_fee'] * deal['c_rate'], 2) if deal['c_rate'] else 0
            deal['income_rub'] = deal['c_amount_rub'] if deal['qty'] >= 0 else deal['o_amount_rub']
            deal['income'] = deal['c_amount'] if deal['qty'] >= 0 else deal['o_amount']
            deal['spending_rub'] = deal['o_amount_rub'] if deal['qty'] >= 0 else deal['c_amount_rub']
            deal['spending_rub'] = deal['spending_rub'] + deal['o_fee_rub'] + deal['c_fee_rub']
            deal['spending'] = deal['o_amount'] if deal['qty'] >= 0 else deal['c_amount']
            deal['spending'] = deal['spending'] + deal['o_fee'] + deal['c_fee']
            deal['profit_rub'] = deal['income_rub'] - deal['spending_rub']
            deal['profit'] = deal['income'] - deal['spending']

            self.add_report_row(row, deal, even_odd=data_row)
            self.add_report_row(row + 1, deal, even_odd=data_row, alternative=1)

            # TODO replace 'us' with value depandable on broker account
            if self.statement is not None:
                self.statement.add_stock_profit('us', self.broker_name, deal['c_date'], self.account_currency,
                                                deal['income'], deal['income_rub'], deal['spending_rub'],
                                                deal['c_rate'])
            data_row = data_row + 1
        row = start_row + (data_row * 2)

        self.reports_xls.add_totals_footer(self.current_sheet, start_row, row, [11, 12, 13, 14, 15])
        return row + 1

    # -----------------------------------------------------------------------------------------------------------------------
    def prepare_derivatives(self):
        # Take all actions without conversion
        query = executeSQL(self.db,
                           "SELECT s.name AS symbol, d.qty AS qty, "
                           "o.timestamp AS o_date, qo.quote AS o_rate, o.settlement AS os_date, "
                           "qos.quote AS os_rate, o.price AS o_price, o.qty AS o_qty, o.fee AS o_fee, "
                           "c.timestamp AS c_date, qc.quote AS c_rate, c.settlement AS cs_date, "
                           "qcs.quote AS cs_rate, c.price AS c_price, c.qty AS c_qty, c.fee AS c_fee "
                           "FROM deals AS d "
                           "JOIN sequence AS os ON os.id=d.open_sid AND os.type = 3 "
                           "LEFT JOIN trades AS o ON os.operation_id=o.id "
                           "JOIN sequence AS cs ON cs.id=d.close_sid AND cs.type = 3 "
                           "LEFT JOIN trades AS c ON cs.operation_id=c.id "
                           "LEFT JOIN assets AS s ON o.asset_id=s.id "
                           "LEFT JOIN accounts AS a ON a.id = :account_id "
                           "LEFT JOIN t_last_dates AS ldo ON o.timestamp=ldo.ref_id "
                           "LEFT JOIN quotes AS qo ON ldo.timestamp=qo.timestamp AND a.currency_id=qo.asset_id "
                           "LEFT JOIN t_last_dates AS ldos ON o.settlement=ldos.ref_id "
                           "LEFT JOIN quotes AS qos ON ldos.timestamp=qos.timestamp AND a.currency_id=qos.asset_id "
                           "LEFT JOIN t_last_dates AS ldc ON c.timestamp=ldc.ref_id "
                           "LEFT JOIN quotes AS qc ON ldc.timestamp=qc.timestamp AND a.currency_id=qc.asset_id "
                           "LEFT JOIN t_last_dates AS ldcs ON c.settlement=ldcs.ref_id "
                           "LEFT JOIN quotes AS qcs ON ldcs.timestamp=qcs.timestamp AND a.currency_id=qcs.asset_id "
                           "WHERE c.timestamp>=:begin AND c.timestamp<:end AND d.account_id=:account_id "
                           "AND s.type_id == 6 "  # To select only derivatives
                           "ORDER BY o.timestamp, c.timestamp",
                           [(":begin", self.year_begin), (":end", self.year_end), (":account_id", self.account_id)])
        start_row = self.data_start_row
        data_row = 0
        while query.next():
            deal = readSQLrecord(query, named=True)
            row = start_row + (data_row * 2)
            if not self.use_settlement:
                deal['os_rate'] = deal['o_rate']
                deal['cs_rate'] = deal['c_rate']
            deal['o_type'] = "Покупка" if deal['qty'] >= 0 else "Продажа"
            deal['c_type'] = "Продажа" if deal['qty'] >= 0 else "Покупка"
            deal['o_amount'] = round(deal['o_price'] * abs(deal['qty']), 2)
            deal['o_amount_rub'] = round(deal['o_amount'] * deal['os_rate'], 2) if deal['os_rate'] else 0
            deal['c_amount'] = round(deal['c_price'] * abs(deal['qty']), 2)
            deal['c_amount_rub'] = round(deal['c_amount'] * deal['cs_rate'], 2) if deal['cs_rate'] else 0
            deal['o_fee'] = deal['o_fee'] * abs(deal['qty'] / deal['o_qty'])
            deal['c_fee'] = deal['c_fee'] * abs(deal['qty'] / deal['c_qty'])
            deal['o_fee_rub'] = round(deal['o_fee'] * deal['o_rate'], 2) if deal['o_rate'] else 0
            deal['c_fee_rub'] = round(deal['c_fee'] * deal['c_rate'], 2) if deal['c_rate'] else 0
            deal['income_rub'] = deal['c_amount_rub'] if deal['qty'] >= 0 else deal['o_amount_rub']
            deal['income'] = deal['c_amount'] if deal['qty'] >= 0 else deal['o_amount']
            deal['spending_rub'] = deal['o_amount_rub'] if deal['qty'] >= 0 else deal['c_amount_rub']
            deal['spending_rub'] = deal['spending_rub'] + deal['o_fee_rub'] + deal['c_fee_rub']
            deal['spending'] = deal['o_amount'] if deal['qty'] >= 0 else deal['c_amount']
            deal['spending'] = deal['spending'] + deal['o_fee'] + deal['c_fee']
            deal['profit_rub'] = deal['income_rub'] - deal['spending_rub']
            deal['profit'] = deal['income'] - deal['spending']

            self.add_report_row(row, deal, even_odd=data_row)
            self.add_report_row(row + 1, deal, even_odd=data_row, alternative=1)

            # TODO replace 'us' with value depandable on broker account
            if self.statement is not None:
                self.statement.add_derivative_profit('us', self.broker_name, deal['c_date'], self.account_currency,
                                                     deal['income'], deal['income_rub'], deal['spending_rub'],
                                                     deal['c_rate'])
            data_row = data_row + 1
        row = start_row + (data_row * 2)

        self.reports_xls.add_totals_footer(self.current_sheet, start_row, row, [11, 12, 13, 14, 15])
        return row + 1

    # -----------------------------------------------------------------------------------------------------------------------
    def prepare_broker_fees(self):
        query = executeSQL(self.db,
                           "SELECT a.timestamp AS payment_date, d.sum AS amount, d.note AS note, q.quote AS rate "
                           "FROM actions AS a "
                           "LEFT JOIN action_details AS d ON d.pid=a.id "
                           "LEFT JOIN accounts AS c ON c.id = :account_id "
                           "LEFT JOIN t_last_dates AS ld ON a.timestamp=ld.ref_id "
                           "LEFT JOIN quotes AS q ON ld.timestamp=q.timestamp AND c.currency_id=q.asset_id "
                           "WHERE a.timestamp>=:begin AND a.timestamp<:end AND a.account_id=:account_id",
                           [(":begin", self.year_begin), (":end", self.year_end), (":account_id", self.account_id)])
        row = start_row = self.data_start_row
        while query.next():
            fee = readSQLrecord(query, named=True)
            fee['amount'] = -fee['amount']
            fee['amount_rub'] = round(fee['amount'] * fee['rate'], 2) if fee['rate'] else 0
            self.add_report_row(row, fee, even_odd=row)
            row += 1
        self.reports_xls.add_totals_footer(self.current_sheet, start_row, row, [3, 4])
        return row + 1

    # -----------------------------------------------------------------------------------------------------------------------
    def prepare_corporate_actions(self):
        # get list of all deals that were opened with corp.action and closed by normal trade
        query = executeSQL(self.db,
                           "SELECT d.open_sid AS sid, s.name AS symbol, d.qty AS qty, "
                           "t.timestamp AS t_date, qt.quote AS t_rate, t.settlement AS s_date, qts.quote AS s_rate, "
                           "t.price AS price, t.fee AS fee "
                           "FROM deals AS d "
                           "JOIN sequence AS os ON os.id=d.open_sid AND os.type = 5 "
                           "JOIN sequence AS cs ON cs.id=d.close_sid AND cs.type = 3 "
                           "LEFT JOIN trades AS t ON cs.operation_id=t.id "
                           "LEFT JOIN assets AS s ON t.asset_id=s.id "
                           "LEFT JOIN accounts AS a ON a.id = :account_id "
                           "LEFT JOIN t_last_dates AS ldt ON t.timestamp=ldt.ref_id "
                           "LEFT JOIN quotes AS qt ON ldt.timestamp=qt.timestamp AND a.currency_id=qt.asset_id "
                           "LEFT JOIN t_last_dates AS ldts ON t.settlement=ldts.ref_id "
                           "LEFT JOIN quotes AS qts ON ldts.timestamp=qts.timestamp AND a.currency_id=qts.asset_id "
                           "WHERE t.timestamp>=:begin AND t.timestamp<:end AND d.account_id=:account_id "
                           "ORDER BY t.timestamp",
                           [(":begin", self.year_begin), (":end", self.year_end), (":account_id", self.account_id)])

        row = self.data_start_row
        even_odd = 1
        while query.next():
            sale = readSQLrecord(query, named=True)
            sale['operation'] = "Продажа"
            sale['amount'] = round(sale['price'] * sale['qty'], 2)
            if sale['s_rate']:
                sale['amount_rub'] = round(sale['amount'] * sale['s_rate'], 2)
            else:
                sale['amount_rub'] = 0
            if sale['t_rate']:
                sale['fee_rub'] = round(sale['fee'] * sale['t_rate'], 2)
            else:
                sale['fee_rub'] = 0

            self.add_report_row(row, sale, even_odd=even_odd)
            row = row + 1

            row, qty = self.proceed_corporate_action(sale['sid'], sale['qty'], 1, row, even_odd)

            even_odd = even_odd + 1
            row = row + 1
        return row

    def proceed_corporate_action(self, sid, qty, level, row, even_odd):
        row, qty = self.output_corp_action(sid, qty, level, row, even_odd)
        row, qty = self.next_corporate_action(sid, qty, level + 1, row, even_odd)
        return row, qty

    def next_corporate_action(self, sid, qty, level, row, even_odd):
        # get list of deals that were closed as result of current corporate action
        open_query = executeSQL(self.db, "SELECT d.open_sid AS open_sid, os.type AS op_type "
                                         "FROM deals AS d "
                                         "JOIN sequence AS os ON os.id=d.open_sid AND (os.type = 3 OR os.type = 5) "
                                         "WHERE d.close_sid = :sid "
                                         "ORDER BY d.open_sid",
                                [(":sid", sid)])
        while open_query.next():
            open_sid, op_type = readSQLrecord(open_query)

            if op_type == TransactionType.Trade:
                row, qty = self.output_purchase(open_sid, qty, level, row, even_odd)
            elif op_type == TransactionType.CorporateAction:
                row, qty = self.proceed_corporate_action(open_sid, qty, level, row, even_odd)
            else:
                assert False
        return row, qty

    def output_purchase(self, sid, proceed_qty, level, row, even_odd):
        if proceed_qty <= 0:
            return row, proceed_qty

        purchase = readSQL(self.db,
                           "SELECT s.name AS symbol, d.qty AS qty, t.timestamp AS t_date, qt.quote AS t_rate, "
                           "t.settlement AS s_date, qts.quote AS s_rate, t.price AS price, t.fee AS fee "
                           "FROM sequence AS os "
                           "JOIN deals AS d ON os.id=d.open_sid AND os.type = 3 "
                           "LEFT JOIN trades AS t ON os.operation_id=t.id "
                           "LEFT JOIN assets AS s ON t.asset_id=s.id "
                           "LEFT JOIN accounts AS a ON a.id = t.account_id "
                           "LEFT JOIN t_last_dates AS ldt ON t.timestamp=ldt.ref_id "
                           "LEFT JOIN quotes AS qt ON ldt.timestamp=qt.timestamp AND a.currency_id=qt.asset_id "
                           "LEFT JOIN t_last_dates AS ldts ON t.settlement=ldts.ref_id "
                           "LEFT JOIN quotes AS qts ON ldts.timestamp=qts.timestamp AND a.currency_id=qts.asset_id "
                           "WHERE os.id = :sid",
                           [(":sid", sid)], named=True)
        purchase['operation'] = ' ' * level * 3 + "Покупка"
        deal_qty = purchase['qty']
        purchase['qty'] = proceed_qty if proceed_qty < deal_qty else deal_qty
        purchase['amount'] = round(purchase['price'] * purchase['qty'], 2)
        purchase['amount_rub'] = round(purchase['amount'] * purchase['s_rate'], 2) if purchase['s_rate'] else 0
        purchase['fee'] = purchase['fee'] * purchase['qty'] / deal_qty
        purchase['fee_rub'] = round(purchase['fee'] * purchase['t_rate'], 2) if purchase['t_rate'] else 0

        self.add_report_row(row, purchase, even_odd=even_odd)
        return row + 1, proceed_qty - purchase['qty']

    def output_corp_action(self, sid, proceed_qty, level, row, even_odd):
        if proceed_qty <= 0:
            return row, proceed_qty

        action = readSQL(self.db, "SELECT a.timestamp AS a_date, a.type, s1.name AS symbol, a.qty AS qty, "
                                  "s2.name AS symbol_new, a.qty_new AS qty_new, a.note AS note "
                                  "FROM sequence AS os "
                                  "JOIN deals AS d ON os.id=d.open_sid AND os.type = 5 "
                                  "LEFT JOIN corp_actions AS a ON os.operation_id=a.id "
                                  "LEFT JOIN assets AS s1 ON a.asset_id=s1.id "
                                  "LEFT JOIN assets AS s2 ON a.asset_id_new=s2.id "
                                  "WHERE os.id = :open_sid ",
                         [(":open_sid", sid)], named=True)
        action['operation'] = ' ' * level * 3 + "Корп. действие"
        qty_before = action['qty'] * proceed_qty / action['qty_new']
        qty_after = proceed_qty
        action['description'] = self.CorpActionText[action['type']].format(old=action['symbol'],
                                                                           new=action['symbol_new'],
                                                                           before=qty_before, after=qty_after)
        self.add_report_row(row, action, even_odd=even_odd, alternative=1)
        return row + 1, qty_before
