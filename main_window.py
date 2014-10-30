from PySide.QtGui import *
from PySide.QtCore import *
import sys
from pymongo import MongoClient
from datetime import datetime
import ast
import os
from breedingTableModel import breedingTableModel
#import subprocess


def data_to_str(data):
    if isinstance(data,(str,unicode)):
        return data
    elif isinstance(data,(int,float)):
        return str(data)
    elif isinstance(data, datetime):
        return str(data.date())

def clear_doc_values(doc):
    '''Sets all values in hierarchical dictionary to None'''
    for key in doc.keys():
        if type(doc[key]) == dict:
            clear_doc_values(doc[key])
        else:
            doc[key] = None

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.client = None
        self.db = None
        self.initUI()
        self.connectDatabase('trex',27017,'test_db')

    def initUI(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction('Exit', qApp.quit)
        self.toolbar.addAction('Connect', self.showConnectionDialog)
        self.tab_widget = QTabWidget()

        self.breeding_tab = breedingTab()
        self.bird_tab = birdTab()

        self.tab_widget.addTab(self.breeding_tab,'Breeding')
        self.tab_widget.addTab(self.bird_tab, 'Birds')

        self.setCentralWidget(self.tab_widget)
        self.resize(800,600)
        self.show()

    def showConnectionDialog(self):
        dialog = connectionDialog()
        if dialog.exec_() == QDialog.Accepted:
            try:
                hostname = dialog.hostname.text()
                port = int(dialog.port.text())
                db_name = dialog.db_name.text()
                self.connectDatabase(hostname, port, db_name)
            except Exception as e:
                print(e.message)
                QMessageBox.critical(self,"Connection Error", "Could not connect to database")

        self.bird_tab.setCollection(self.db.birds)
        self.breeding_tab.setCollection(self.db.breeding)

    def connectDatabase(self, hostname, port, db_name):
        self.client = MongoClient(hostname, port)
        self.db = self.client[db_name]
        self.bird_tab.setCollection(self.db.birds)
        self.breeding_tab.setCollection(self.db.breeding)

class recordingsList(QListWidget):
    def __init__(self, *args, **kwargs):
        super(recordingsList, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomConextMenuRequested)
    
    def onCustomConextMenuRequested(self, pos):
        menu = QMenu(self)
        menu.setParent(self)
        openAction = QAction("Open with Arfview", menu)
        openAction.triggered.connect(self.open_selected)
        copyAction = QAction("Copy", menu)
        openAction.triggered.connect(self.copy_selected)
        menu.addAction(openAction)
        menu.addAction(copyAction)
        menu.exec_(self.mapToGlobal(pos))

    def open_selected(self):
        file = self.selectedItems()[0].text()
        os.system('ssh kkong -Y arfview %s'%file)
    #subprocess.call(('ssh kkong -Y arfview %s'%file).split())

    def copy_selected(self):
        pass

class birdTab(QWidget):
    def __init__(self, collection=None):
        super(birdTab,self).__init__()
        self.initUI()
        self.setCollection(collection)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        #self.table.setSortingEnabled(False)
        self.table.setStyleSheet("QTableWidget::item{selection-background-color: red}")
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.toolbar = QToolBar()
        self.toolbar.addWidget(QLabel("find({"))
        self.query_edit = QLineEdit()
        self.toolbar.addWidget(self.query_edit)
        self.toolbar.addWidget(QLabel("})"))
        self.toolbar.addAction('Query', self.queryPressed)
        self.toolbar.addAction('Save', self.save)
        self.toolbar.addAction('Discard Changes', self.discard)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.toolbar)
        self.setLayout(self.layout)
    
    def setCollection(self, collection):
        self.collection = collection
        if collection is not None:
            self.setQuery('')

    def setQuery(self, query):
        '''Sets the current query whose results are shown in the table'''
        query_dict = ast.literal_eval(''.join(['{',query,'}']))
        cursor = self.collection.find(query_dict)
        self.populateTable(cursor)
        self.query_edit.setText(query)
        
    def populateTable(self, cursor):
        '''The bird table contains data from a mongo query.  The results of the 
            query are passed to the function as a cursor object.'''
        
        self.table.setRowCount(cursor.count())
        self.table.setVerticalHeaderLabels([str(i) for i in xrange(1,cursor.count()+1)])
        column_names = list(set(field for doc in cursor for field in doc.keys() 
                                if field not in ('name','_id','recordings')))
        column_names.insert(0,'name') #ensures that 'name' is first column 
        column_names.insert(len(column_names),'recordings')
        self.table.setColumnCount(len(column_names))
        self.table.setHorizontalHeaderLabels(column_names)
        cursor.rewind()
        self.recording_lists = []
        for row,doc in enumerate(cursor):
            for column in xrange(self.table.columnCount()):
                field = self.table.horizontalHeaderItem(column).text()
                data = doc.get(field)
                if field == 'recordings' and type(data)==list:
                    new_list = recordingsList()
                    for recording in data:
                        new_list.addItem(recording)
                    self.recording_lists.append(new_list)
                    self.table.setCellWidget(row,column,new_list)
                else:
                    item = QTableWidgetItem(data_to_str(data))  
                    self.table.setItem(row,column,item)  
                    self.table.setColumnWidth(column,200)
                    self.table.setRowHeight(row, 40)


    def queryPressed(self):
        self.setQuery(self.query_edit.text())

    def save(self):
        pass

    def discard(self):
        pass
        

class breedingTab(QDialog):
    def __init__(self, collection=None):
        super(breedingTab,self).__init__()
        self.initUI()  
        self.setCollection(collection)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.table = QTableView()#QTableWidget()
        self.table.setSortingEnabled(False)
        self.table.setStyleSheet("QTableWidget::item{selection-background-color: red}")
        #self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.toolbar = QToolBar()
        self.toolbar.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.toolbar.addWidget(self.date_edit)
        # self.toolbar.addAction('Save', self.save)
        # self.toolbar.addAction('Discard Changes', self.discard)
        self.toolbar.addAction(QIcon('icons/edit-undo.png'),'Undo', self.undo)
        self.toolbar.addAction(QIcon('icons/edit-redo.png'),'Redo', self.redo)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.toolbar)
        self.setLayout(self.layout)

    def setCollection(self, collection):
        self.collection = collection
        if collection is not None:
            #creating model
            model = breedingTableModel(self.collection)
            model.dateChanged.connect(self.date_edit.setDate)
            self.date_edit.setDate(model.date)
            self.date_edit.dateChanged.connect(model.setDate)
            self.table.setModel(model)
#            self.date_edit.setDateTime(last_date)

    def populateTable(self,doc):
        '''Adds breeding information to the breeding table.  The breeding info for a single day
        is represented by a single hierarchical document, which will be used to fill the entire
        table with the data for each nest'''
        row_names = [key for key in doc.keys() if key not in ('date','_id')]
        row_names.sort()
        self.table.setRowCount(len(row_names))
        for row,name in enumerate(row_names): 
            header = QTableWidgetItem(name)
            header.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.table.setVerticalHeaderItem(row, header)
        column_names = list(set(field for n in row_names for field in doc[n].keys()))
        self.table.setColumnCount(len(column_names))
        self.table.setHorizontalHeaderLabels(column_names)
        for row in xrange(self.table.rowCount()):
            for column in xrange(self.table.columnCount()):
                nest = self.table.verticalHeaderItem(row).text()
                field = self.table.horizontalHeaderItem(column).text()
                data = doc[nest][field]
                item = QTableWidgetItem(data_to_str(data))
                self.table.setItem(row,column,item)   

    def undo(self):
        model = self.table.model() 
        if model is not None:
            model.undo_stack.undo()
            
    def redo(self):
        model = self.table.model() 
        if model is not None:
            model.undo_stack.redo()

    # def save(self):
    #     for column in len(self.table.columnCount()):
    #         for row in len(self.table.rowCount()):
    #             self.table.item(row,columnt).text()

    # def discard(self):
    #     pass 

class connectionDialog(QDialog):
    def __init__(self):
        super(connectionDialog,self).__init__()
        self.initUI()

    def initUI(self):
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Hostname:"),0,0)
        self.layout.addWidget(QLabel("Port:"),1,0)
        self.layout.addWidget(QLabel("Database Name:"),2,0)
        self.hostname = QLineEdit()
        self.port = QLineEdit("27017")
        self.db_name = QLineEdit()
        self.layout.addWidget(self.hostname,0,1)
        self.layout.addWidget(self.port,1,1)
        self.layout.addWidget(self.db_name,2,1)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box, 3,1)
        self.setLayout(self.layout)


   
        

# class breedingModel(QAbstractTableModel):
#     def __init__(self, doc):
#         super(QAbstractTableModel, self).__init__()
#         self.client = None
#         self.db = None
#         self.doc = doc
#         self.row_names = [key for key in doc.keys() if key not in ('date','_id')]
#         self.row_names.sort()
#         self.column_names = list(set(field for n in row_names for field in doc[n].keys()))
#         self.connectDatabase('trex',27017,'test_db')

#     def connectDatabase(self, hostname, port, db_name):
#         self.client = MongoClient(hostname, port)
#         self.db = self.client[db_name]
        
#     def columnCount(self):
#         return len(self.column_names)

#     def rowCount(self):
#         return len(self.row_names)



if __name__=='__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Bird DB Interface")
    mainWin = MainWindow()
    sys.exit(app.exec_())
    