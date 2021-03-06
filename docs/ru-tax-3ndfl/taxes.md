### Инструкция по подготовке данных для декларации 3-НДФЛ для Interactive Brokers

*Данная инструкция представлена здесь в ознакомительных целях. Скриншоты ниже представлены на английском языке, но вы можете выбрать русский в программе (для смены языка с Английского на Русский нужно выбрать пункт меню Languages->Russian и перезапустить программу).
Данное програмное обеспечение было создано для использования в личных целях и большая часть расчетов тестировалась с дивидендами и длинными позициями в долларах.  
Другие валюта, а так же короткие продажи, операции с опционами, корпоративных событие и специфические комиссии Interactive Brokers поддерживаются, но могут иметь недочёты, т.к. у меня не было достаточного количества примеров, чтобы протестировать все варианты.*


*Вы можете использовать его свободно, но с обязательной ссылкой на https://github.com/titov-vv/jal в случае публикации в сети Интернет   
Информация об ошибках, замечания и пожелания приветствуются. Помимо Github связаться со мной и задать вопросы можно по адресу [jal@gmx.ru](mailto:jal@gmx.ru?subject=%5BJAL%5D%20Tax%20report)*


1. Нужно получить flex-отчет по всем операциям в формате XML.  
Для этого необходимо в личном кабинете Interactive Brokers выбрать раздел *Reports / Tax Docs*. 
На появившейся странице *Reports* нужно выбрать закладку *Flex Queries*. В разделе *Activity Flex Query* нужно нажать *'+'* чтобы создать новый отчёт.
Далее необходимо выполнить настройку отчета:
    - *Query name* - нужно указать уникальное имя отчёта
    - *Sections* - нужно отменить необходимые секции отчета. Минимально необходимы: *Account Information, Cash Transactions, Corporate Actions, Securities Info, Trades, Transactions Fees, Transfers*
    - *Format* - XML
    - *Date Format* - yyyyMMdd
    - *Time Format* - HHmmss
    - *Date/Time separator* - ;(semi-colon)
    - *Profit and Loss* - Default
    - на вопросы *Include Canceled Trades?, Include Currency Rates?, Display Account Alias in Place of Account ID?, Breakout by Day?* ответить No.  
    После этого нажать *Continue* и затем *Create*  
2. Вновь созданный flex-отчет появится в списке *Activity Flex Query*. Его нужно запустить по нажатию на стрелку вправо (команда *Run*).
Формат нужно оставить XML. В качестве периодна максимум можно выбрать год - поэтому нужно выполнить отчет несколько раз, чтобы последовательно получить операции за всё время существования счёта.
В результате у вас будет один или несколько XML файлов с отчетами. В качестве примера для дальнейших действий я буду использовать [IBKR_flex_sample.xml](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/IBKR_flex_sample.xml)
3. В *jal* все транзакции привязаны к тому или иному счету. Поэтому для успешной загрузки отчёта вам нужно заранее создать как минимум пару счетов через меню *Data->Accounts* (в русской версии *Данные->Счета*):
    - счет типа *Investment*, у которого номер и валюта будут совпадать с номером и валютой счета Interactive Brokers. В моём примере я использую U1234567 и USD:  
    ![IBRK account](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/ibkr_account.png?raw=true) 
    - ещё один счет любого типа - он будет необходим для учета транзакций ввода/вывода дережных средств. Например:  
    ![Bank account](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/bank_account.png?raw=true)  
    - если вы производили операции в других валютах, то нужно добавить счета с таким же номером, но другой валютой (например, если для конвертации долларов из рублей мне бы понадобился счет U1234567, RUB)
(При отсутствии нужного счёта вы получите ошибку *ERROR - Failed to load attribute: accountId* при импорте) 
4. Непосредственно для загрузки отчёта вам необходимо выбрать пункт меню *Import->Broker statement...* (в русской версии *Импорт->Отчет брокера...*), после чего указать XML файл, который необходимо загрузить.
Если ваш отчет содержит транзации ввода/вывода денежных средств, то вы *jal* попросит вас указать какой счет нужно использовать для списания/зачисленя этих средств, например:  
![Select account](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/account_selection.png?raw=true)  
В случае успешного импорта, вы увидите сообщение *IB Flex-statement loaded successfully* на закладке *Log messages* (в русской версии *Сообщения*)  
![Import success](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/import_log.png?raw=true)
5. После загрузки вы можете выбрать полный интервал времени и нужный счёт, чтобы проверить корректность импорта данных:  
![Main window](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/main_window.png?raw=true)  
Хорошим индикатором может служить совпадение конечного баланса счёта.  
Возможны необольшие отклонения, у меня они составляют несколько центов. Они связаны с тем, что Interactive Brokers округляют налог в отчётах - чтобы исправить это вы можете проголосовать по [этой ссылке](https://interactivebrokers.com/en/general/poll/featuresPoll.php?sid=15422). 
6. При подготовке декларации все суммы нужно пересчитать в рубли - для этого необходимо загрузить курсы валют.
Сделать это можно с помощью меню *Load->Load quotes...* (в русской версии *Загрузить->Загрузить Котировки...*) и указав необходимый диапазон дат:  
![Quotes](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/update_quotes.png?raw=true)
7. С помощью *jal* вы можете подготовить как просто расчёт в виде файла Excel, так и автоматически занести данные в файл программы *"Декларация 2020"*. 
Все шаги, связанные с программой *"Декларация 2020"* и файлами *.dc0* являются необязательными и вы можете их пропустить.
Формат файла программы *"Декларация"* не является открытым и меняется каждый год, поэтому сначала вам нужно создать пустой файл.
Для этого вам необходимо заполнить 2 страницы программы *"Декларация"*:
    - *Задание условий* - нужно указать номер инспекции и ОКТМО по месту жительства. **Обязательно** нужно поставить галочку *Имеются доходы->В иностранной валюте*  
    ![Declaration Conditions](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/declaration_1.png?raw=true)
    - *Сведения о декларанте* - нужно указать ФИО, дату/место рождения и сведения о документе, удостоверящем личность
    ![Declaration Person](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/declaration_2.png?raw=true)   
После этого вы сможете сохранить результат в файл (я назвал его *declaration_empty.dc0*)
8. Для выполнения расчёта вам необходимо выбрать пункт меню *Reports->Tax Report \[RU]* (в русской версии *Отчёты->Налоговый отчёт \[RU]*) и заполнить параметры в появившемся диалоговом окне:  
![Report parameters](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_params.png?raw=true)  
Вам необходимо задать:
    - год за который формируется отчёт (2020)
    - счёт, который содержит операции, которые нужно включить в отчёт (в моём примере *IBKR*)
    - имя файла Excel, куда будет сохранён отчёт
    - поставить галочку *Update file "Декларация" \(.dc0)*, если вы хотите внести данные в файл программы *"Декларация 2020"*
    - *Initial file* - здесь нужно выбрать пустой файл декларации, который был создан в п.7
    - *Output file* - тут нужно указать имя файла, куда будет сохранена обновлённая декларация
    - *Update only information about dividends* - существуют разные практики занесения информации о сделках в декларацию. 
    Поэтому если вы не хотите, чтобы каждая сделка добавлялась отдельным листом - поставьте эту галочку и в файл будет добавлена лишь информация о дивидендах.
Нажмите кнопку *OK* - в случае успешного выполнения на диске будут записаны соответствующие файлы
9. Если вы выбирали обновление файла декларации, то вы можете теперь открыть его с помощью программы *"Декларация 2020"* и проверить, что информация была добавлена на закладку *Доходы за пределами РФ*  
![Declaration Updated](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/declaration_3.png?raw=true)
10. [Получившийся Excel-файл с расчётом](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/3ndfl_tax_report.xlsx) <sup>1</sup> содержит 4 закладки:  
    - Расчёт дивидендов  
    ![Report Dividends](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_1.png?raw=true)
    - Расчёт сделок с ценными бумагами 
    ![Report Deals](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_2.png?raw=true)
    - Расчёт сделок с производными финансовыми инструментами
    ![Report Derivatives](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_3.png?raw=true)
    - Расчёт комиссий и прочих операций  
    ![Report Fees](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_4.png?raw=true)
    - Расчёт по корпоративным событиям  
    ![Report Corporate Actions](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/img/report_5.png?raw=true)

<sup>1</sup> - при использовании *OpenOffice Calc* вы можете увидеть одни нули в строке *"ИТОГО"* - это известная особенность, *OpenOffice Calc* не пересчитывает формулы при открытии файла. Перерасчёт формул можно инициировать нажанием *F9* или изменением настроек в меню Tools -> Cell Contents -> AutoCalculate.     

[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Ftitov-vv%2Fjal%2Fblob%2Fmaster%2Fdocs%2Fru-tax-3ndfl%2Ftaxes.md&count_bg=%23B981DD&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=tax&edge_flat=false)](https://hits.seeyoufarm.com)
