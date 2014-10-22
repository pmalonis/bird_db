from PySide.QtGui import *
from PySide.QtCore import *
import sys
from pymongo import MongoClient
import datetime

def data_to_str(data):
    if isinstance(data,(str,unicode)):
        return data
    elif isinstance(data,(int,float)):
        return str(data)
    elif isinstance(data, datetime):
        return str(data.date())

class MainWindow(QMainWindow):
    def __init__(self, ):
        super(MainWindow, self).__init__()
        self.client = None
        self.db = None
        self.connectDatabase('trex',27017,'test_db')
        self.initUI()

    def connectDatabase(self, hostname, port, db_name):
        self.client = MongoClient('trex',27017)
        self.db = self.client[db_name]

    def initUI(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.exit_action = QAction('Exit', self)
        #self.exit_action.triggered.connect(qApp.quit)
        self.toolbar.addAction(self.exit_action)
        self.tab_widget = QTabWidget()

        # breeding tab
        self.breeding_table = QTableWidget()
        self.breeding_table.setSortingEnabled(False)
        self.tab_widget.addTab(self.breeding_table, 'Breeding')
        
        # bird tab
        self.bird_table = QTableWidget()
        self.bird_table.setSortingEnabled(False)
        self.tab_widget.addTab(self.bird_table, 'Birds')
        self.setCentralWidget(self.tab_widget)
        self.show()

    def populateBreeding(self,doc):
        row_names = [key for key in doc.keys() if key not in ('date','_id')]
        row_names.sort()
        self.breeding_table.setRowCount(len(row_names))
        self.breeding_table.setVerticalHeaderLabels(row_names)
        column_names = list(set(field for n in row_names for field in doc[n].keys()))
        self.breeding_table.setColumnCount(len(column_names))
        self.breeding_table.setHorizontalHeaderLabels(column_names)
        for row in xrange(self.breeding_table.rowCount()):
            for column in xrange(self.breeding_table.columnCount()):
                nest = self.breeding_table.verticalHeaderItem(row).text()
                field = self.breeding_table.horizontalHeaderItem(column).text()
                data = doc[nest][field]
                cellWidget = QLabel(data_to_str(data))
                self.breeding_table.setCellWidget(row,column,cellWidget)   
            
    
if __name__=='__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Bird DB Interface")
    mainWin = MainWindow()
    sys.exit(app.exec_())
    