::pyuic6 -x main_window.ui -o MainWindow.py
pyuic6 -x setting_dialog.ui -o Ui_SettingDialog.py

::pyrcc5 icons.qrc -o IconsRc.py
::pyuic5 -x main.ui -o ../main_window.py --import-from=views
