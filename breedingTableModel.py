from PySide.QtCore import *
from PySide.QtGui import *
from datetime import datetime

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


class CommandSetDate(QUndoCommand):
    def __init__(self, date, model, fromDateEdit):
        super(CommandSetDate, self).__init__()
        self.model = model
        self.new_date = date
        self.fromDateEdit = fromDateEdit
        if hasattr(model, 'date'):
            self.old_date = model.date
        else:
            self.old_date = None

    def setModelDate(self, date):
        '''Sets the currently visible date to the date represented by a qdatetime'''
        if isinstance(date, QDate):
            python_dt = datetime.combine(date.toPython(), datetime.min.time())
        elif isinstance(date, QDateTime):
            python_dt = date.toPython()
        elif isinstance(date, datetime):
            python_dt = date
        else:
            raise TypeError('date argument must be python datetime or QDateTime')
            
        self.model.beginResetModel()
        
        if hasattr(self.model,'date') and self.model.doc() is not None:
            doc = self.model.doc()
            tableUnedited = all([value==None for row in doc.keys() if 
                                 row not in ('date', '_id') for value in doc[row].itervalues()])
            if tableUnedited:
                self.model.collection.remove({'date':self.model.date})
        self.model.date = python_dt
        # creating new document for date with fields of closest date
        if self.model.collection.find_one({'date':python_dt}) is None:  
            id = self.model.collection.insert({})
            template = self.model.collection.find_one({'date':{'$lt':python_dt}},sort=[('date',-1)])
            if template is None:
                template = self.model.collection.find_one({'date':{'$gt':python_dt}},sort=[('date',1)])

            clear_doc_values(template)
            template.pop('_id')
            template.update(date=self.model.date)
            self.model.collection.update({'_id':id},template)

        self.model.endResetModel()
        if not self.fromDateEdit: #prevents circular signal connection
            self.model.dateChanged.emit(date)

    def redo(self):
        self.setModelDate(self.new_date)
        if self.fromDateEdit: #after first call of function the date edit can't trigger this command again
            self.fromDateEdit = False

    def undo(self):
        if self.old_date is not None:
            self.setModelDate(self.old_date)
        
class CommandEdit(QUndoCommand):
    def __init__(self, index, value, model):
        super(CommandEdit, self).__init__()
        self.model = model
        self.index = index 
        self.old_value = self.model.data(index)
        self.new_value = value
        print(self.old_value, self.new_value)

    def setValue(self, value):
        row_name = self.model.rowNames()[self.index.row()]
        column_name = self.model.columnNames()[self.index.column()]
        row = self.model.doc()[row_name]
        row.update({column_name:value})
        print(row)
        self.model.collection.update({'date':self.model.date}, {'$set':{row_name:row}})
        self.model.dataChanged.emit(self.index, self.index)
    
    def redo(self):
        self.setValue(self.new_value)

    def undo(self):
        self.setValue(self.old_value)


class breedingTableModel(QAbstractTableModel):
    '''Model for the breeding table'''

    dateChanged = Signal(datetime)

    def __init__(self, collection):
        '''
        Parameters
        ----------
        doc: dictionary containing a day's breeding records
        collection: mongo collection that contains breeding data
        '''
        super(breedingTableModel, self).__init__()
        self.collection = collection
        self.undo_stack = QUndoStack(self)
        last_date = self.collection.find_one(sort=[('date',-1)])['date']
        self.setDate(last_date, fromDateEdit=False)
    # def setDate(self, date, fromDateEdit=True):
    #     '''Sets the currently visible date to the date represented by a qdatetime'''
    #     if isinstance(date, QDate):
    #         python_dt = datetime.combine(date.toPython(), datetime.min.time())
    #     elif isinstance(date, QDateTime):
    #         python_dt = date.toPython()
    #     elif isinstance(date, datetime):
    #         python_dt = date 
    #     else:
    #         raise TypeError('date argument must be python datetime or QDateTime')
            
    #     self.date = python_dt
    #     doc = self.collection.find_one({'date':python_dt})
    #     if doc == None:  # creating new document for date with fields of closest date
    #         id = self.collection.insert({})
    #         template = self.collection.find_one({'date':{'$lt':python_dt}},sort=[('date',-1)])
    #         if template is None:
    #             template = self.collection.find_one({'date':{'$gt':python_dt}},sort=[('date',1)])

    #         clear_doc_values(template)
    #         template.pop('_id')
    #         self.collection.update({'_id':id},template)
    #         doc = self.collection.find_one({'_id':id})
          
    #     self.setDoc(doc)

    def columnCount(self, parent):
        return len(self.columnNames())
        
    def columnNames(self):
        doc = self.doc()
        if doc is not None:
            column_names = list(set(field for n in self.rowNames()
                                for field in doc[n].keys()))
        else:
            column_names = []
        return column_names

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row_name = self.rowNames()[index.row()]
            column_name = self.columnNames()[index.column()]
            return self.doc()[row_name].get(column_name)

    def doc(self):
        return self.collection.find_one({'date':self.date})

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if len(self.columnNames()) > section:
                    return self.columnNames()[section]
                else:
                    print(self.rowNames(),section)
                    return 0

            elif orientation == Qt.Vertical:
                if len(self.rowNames()) > section:
                    return self.rowNames()[section]
                else:
                    print(self.rowNames(),section)
                    return 0

    def rowCount(self, parent):
        return len(self.rowNames())
        
    def rowNames(self):
        doc = self.doc()
        if doc is not None:
            row_names = [key for key in doc.keys() 
                         if key not in ('date','_id')]
            row_names.sort()
        else:
            row_names = []

        return row_names

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            command = CommandEdit(index, value, self)
            self.undo_stack.push(command)
        return True

    def setDate(self, date, fromDateEdit=True):
        command = CommandSetDate(date, self, fromDateEdit)
        self.undo_stack.push(command)
