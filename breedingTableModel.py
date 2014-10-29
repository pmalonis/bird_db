from PySide.QtCore import *
from PySide.QtGui import *

class breedingTableModel(QAbstractTableModel):
    '''Model for the breeding table'''
    def __init__(self, doc, collection):
        '''
        Parameters
        ----------
        doc: dictionary containing a day's breeding records
        collection: mongo collection that contains breeding data
        '''
        super(birdTableModel, self).__init__()
        self.doc = doc
        self.collection = collection
        self.column_names = list(set(field for n in row_names for field in self.doc[n].keys()))
        self.row_names = [key for key in self.doc.keys() if key not in ('date','_id')]
        self.row_names.sort()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return index.internalPointer()

    def flags(self, index, role):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.column_names[section]
            elif orientation == Qt.Vertical:
                return self.row_names[section]
    
    def index(self, row, column, parent):
        row_name = self.row_names[index.row()]
        column_name = self.column_names[index.column()]
        data = self.doc.get(row_name).get(column_name)
        return self.createIndex(row, column, data)

    
