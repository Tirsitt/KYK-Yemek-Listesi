from PyQt5.QtWidgets import  QApplication,QDialog,QTableWidgetItem,QMessageBox
from PyQt5.uic import loadUi
import sys
import sqlite3


class FirstPage(QDialog):
    def __init__(self):
        super(FirstPage,self).__init__()

        loadUi("1.ui",self)
    
        self.uyeOl.clicked.connect(self.secondPage)

        self.oturumAc.clicked.connect(self.handle_login)
        self.connectDatabase()

    def connectDatabase(self):
        try:
            self.conn = sqlite3.connect('Database.db')
            self.cur = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Veritabanına bağlanılamadı: {e}")
            sys.exit(1)

    def handle_login(self):
        username = self.username.text()
        password = self.password.text()
    
        if not username or not password:
            self.labelError.setText("Kullanıcı adı ve şifre boş bırakılamaz.")
            return   

        query = "SELECT * FROM Password WHERE Username = ? AND Password = ?"
        self.cur.execute(query, (username, password))
        user = self.cur.fetchone()

        if user:        
            self.thirdPage(username)
        else:
            self.labelError.setText("Hata! Hesabınız bulunamadı!")
 
    def secondPage(self):
        self.secondWindow=SecondPage()
        self.secondWindow.show()

    def thirdPage(self,username):
        self.thirdWindow=ThirdPage(username)
        self.thirdWindow.show()
        self.close()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()
    

class SecondPage(QDialog):
    def __init__(self):
        super(SecondPage,self).__init__()
        loadUi("2.ui",self)

        self.uyeOl.clicked.connect(self.handle_signup)
        self.connectDatabase()

    def connectDatabase(self):
        try:
            self.conn = sqlite3.connect('Database.db')
            self.cur = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Veritabanına bağlanılamadı: {e}")
            sys.exit(1)

    def handle_signup(self):
        username = self.username.text()
        password = self.password.text()
        confirm_password = self.confirmPassword.text()

        if not username or not password or not confirm_password:
            self.labelError.setText("Hata! Kullanıcı adı ve şifre boş bırakılamaz.")
            return

        if password != confirm_password:
            self.labelError.setText("Şifreler eşleşmiyor.")
            return


        query = "INSERT INTO Password (Username, Password) VALUES (?, ?)"
        try:
            self.cur.execute("SELECT * FROM Password WHERE Username = ?", (username,))    
            existing_user = self.cur.fetchone()
            if existing_user:
                self.labelError.setText("Kullanıcı adı zaten mevcut.")
                return
            
            query = "INSERT INTO Password (Username, Password) VALUES (?, ?)"
            self.cur.execute(query, (username, password))
            self.conn.commit()
            self.addGoodFoodPlaceholders(username)
            self.labelError.setText("Hesap başarıyla oluşturuldu!")

        except sqlite3.Error as e:
                self.labelError.setText(f"Veritabanı Hatası: {str(e)}")
        
    def addGoodFoodPlaceholders(self, username):
        query = "INSERT INTO GoodFood (Username, FoodItem) VALUES (?, ?)"
        for _ in range(80):
            self.cur.execute(query, (username, None))
        self.conn.commit()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()



class ThirdPage(QDialog):
    def __init__(self,username):
        super(ThirdPage,self).__init__()

        self.username = username

        loadUi("3.ui",self)
        
        self.food_table.setColumnCount(1)
        self.food_table.setRowCount(4)
        self.food_table.setHorizontalHeaderLabels(["Hafta"])
    
        for i, week in enumerate(['Hafta 1', 'Hafta 2', 'Hafta 3', 'Hafta 4']):
            item = QTableWidgetItem(week)
            self.food_table.setItem(i, 0, item)
        
        self.sec.clicked.connect(self.selectWeek)

        self.back.clicked.connect(self.goBack)
        self.back.setVisible(False)   

        self.selectedfoods.setVisible(False)
        self.ara.textChanged.connect(self.searchFood)  
   
        self.addGood.clicked.connect(self.fourthPage)

        self.good.stateChanged.connect(self.toggleGoodFood)
        self.good.setVisible(False)

        self.name.setText("Merhaba " + username)
        self.exit.clicked.connect(self.exitFromPage)

        self.conn = sqlite3.connect('Database.db')
        self.cur = self.conn.cursor()

    def fourthPage(self):
        self.fourthWindow=FourthPage(self.username)
        self.fourthWindow.show()

    def searchFood(self):

        if self.ara.text()=="":
            self.selectedfoods.setVisible(False)
    
        else:
            search_term = self.ara.text().strip() 

            if not search_term:  
                return

            self.cur.execute("PRAGMA table_info(Food)")
            columns = [col[1] for col in self.cur.fetchall()]

            search_conditions = []
            for col in columns:
                search_conditions.append(f"{col} LIKE '%{search_term}%'")
            query = f"SELECT * FROM Food WHERE {' OR '.join(search_conditions)}"

            try:
                self.cur.execute(query)
                rows = self.cur.fetchall()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Sorgu Hatası", f"Sorgu yürütülemedi: {e}")
                return

            output_list = []

            for row in rows:
                matching_data = []
                for col_index, value in enumerate(row):
                    if search_term.lower() in str(value).lower():
                        matching_data.append(f"{columns[col_index]}: {value}")
                if matching_data:  
                    output_list.append(", ".join(matching_data))

            self.selectedfoods.clearContents()
            self.selectedfoods.setRowCount(0)

            if not output_list:
                QMessageBox.information(self, "Ara\\", "Bu arama terimi için sonuç bulunamadı.")
                return

            num_columns = len(output_list[0].split(", "))
            self.selectedfoods.setColumnCount(num_columns)

            column_headers = [item.split(":")[0] for item in output_list[0].split(", ")]
            self.selectedfoods.setHorizontalHeaderLabels(column_headers)

            for row_index, row in enumerate(output_list):
                self.selectedfoods.insertRow(row_index)
                data_items = row.split(", ")
                for col_index, data_item in enumerate(data_items):
                    item = QTableWidgetItem(data_item.split(": ")[1])  
                    self.selectedfoods.setItem(row_index, col_index, item)

            self.selectedfoods.setVisible(True)

    def fetchColumns(self):
        self.cur.execute("PRAGMA table_info(Food)")
        return [col[1] for col in self.cur.fetchall()]

    def constructQuery(self, week):
        start_column = (int(week) - 1) * 5
        end_column = start_column + 5
        columns = self.fetchColumns()
        selected_columns = columns[start_column:end_column]
        query = f"SELECT {', '.join(selected_columns)} FROM Food"
        return query, selected_columns

    def selectWeek(self):
        self.selected_row = self.food_table.currentRow()
        if self.selected_row == -1:
            return  

        self.selected_week = self.food_table.item(self.selected_row, 0).text().split()[1]
        query, selected_columns = self.constructQuery(self.selected_week)

        try:
            self.cur.execute(query)
            rows = self.cur.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Sorgu Hatası", f"Sorgu yürütülemedi: {e}")
            return

        self.populateTable(rows, selected_columns)
        self.back.setVisible(True)  

        self.sec.setVisible(False)   

    def populateTable(self, rows, selected_columns):

        self.food_table.clearContents()

        days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        self.food_table.setColumnCount(len(days_of_week))
        self.food_table.setHorizontalHeaderLabels(days_of_week)

        self.food_table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, col in enumerate(row):
                item = QTableWidgetItem(str(col))
                self.food_table.setItem(i, j, item)
        
        self.good.setVisible(True)

    def goBack(self):
        self.food_table.clearContents()
        self.populateWeeks()

        self.back.setVisible(False) 
        self.sec.setVisible(True)   

    def populateWeeks(self):
        self.food_table.setColumnCount(1)
        self.food_table.setRowCount(4)
        self.food_table.setHorizontalHeaderLabels(["Hafta"])

        for i, week in enumerate(['Hafta 1', 'Hafta 2', 'Hafta 3', 'Hafta 4']):
            item = QTableWidgetItem(week)
            self.food_table.setItem(i, 0, item)
        
        self.good.setVisible(False)


    def toggleGoodFood(self):
        
        if self.good.isChecked():
            self.showGoodFood()
        else:
            query, selected_columns = self.constructQuery(self.selected_week)
            self.cur.execute(query)
            rows = self.cur.fetchall()
            self.populateTable(rows, selected_columns)

            self.good.setVisible(True)

    def showGoodFood(self):
        if self.selected_row == -1:
            QMessageBox.warning(self, "Seçim Hatası", "Lütfen önce bir hafta seçin.")
            return

        query, selected_columns = self.constructQuery(self.selected_week)
        try:
            self.cur.execute(query)
            rows = self.cur.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Sorgu Hatası", f"Sorgu yürütülemedi: {e}")
            return

        self.cur.execute("SELECT FoodItem FROM GoodFood WHERE Username = ? AND FoodItem IS NOT NULL", (self.username,))
        good_food_items = {item[0] for item in self.cur.fetchall()}

        filtered_rows = []
        for row in rows:
            filtered_row = [item if item in good_food_items else "" for item in row]
            filtered_rows.append(filtered_row)

        self.populateTable(filtered_rows, selected_columns)

    def exitFromPage(self):
        self.close()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()



class FourthPage(QDialog):
    def __init__(self,username):
        super(FourthPage,self).__init__()

        self.username = username
        
        loadUi("4.ui",self)

        self.food_table.setColumnCount(1)
        self.food_table.setHorizontalHeaderLabels(["Yemek Listesi"])

        self.goodFood.setColumnCount(1)
        self.goodFood.setHorizontalHeaderLabels(["Seçilen Yemekler"])

        self.ekle.clicked.connect(self.moveRowToGoodFood)
        self.sil.clicked.connect(self.moveRowToFoodTable)

        self.name.setText("Merhaba " + username)
        self.back.clicked.connect(self.exitFromPage)
     
        self.connectDatabase()
        self.populateTableWithData()
        self.loadGoodFoodData()

    def connectDatabase(self):
        try:
            self.conn = sqlite3.connect('Database.db')
            self.cur = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Veritabanına bağlanılamadı: {e}")
            sys.exit(1)

    def populateTableWithData(self):
        try:
            self.cur.execute("SELECT * FROM Food")
            rows = self.cur.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Sorgu Hatası", f"Sorgu yürütülemedi: {e}")
            return

        data = []
        for row in rows:
            for item in row:
                if item is not None:
                    data.append(item)

        self.food_table.setRowCount(len(data))
        for i, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            self.food_table.setItem(i, 0, item)

    def loadGoodFoodData(self):
        query = "SELECT FoodItem FROM GoodFood WHERE Username = ? AND FoodItem IS NOT NULL"
        self.cur.execute(query, (self.username,))
        rows = self.cur.fetchall()

        data = [row[0] for row in rows if row[0] is not None]

        self.goodFood.setRowCount(len(data))
        for i, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            self.goodFood.setItem(i, 0, item)

    def moveRowToGoodFood(self):

        self.selected_row = self.food_table.currentRow()
        if self.selected_row == -1:
            QMessageBox.warning(self, "Seçim Hatası", "Lütfen önce bir satır seçin.")
            return
        self.selected_item = self.food_table.item(self.selected_row, 0).text()


        if hasattr(self, 'selected_row'):
            row_position = self.goodFood.rowCount()
            self.goodFood.insertRow(row_position)
            self.goodFood.setItem(row_position, 0, QTableWidgetItem(self.selected_item))

            self.cur.execute("SELECT rowid FROM GoodFood WHERE Username = ? AND FoodItem IS NULL LIMIT 1", (self.username,))
            rowid = self.cur.fetchone()
            if rowid:
                query = "UPDATE GoodFood SET FoodItem = ? WHERE rowid = ?"
                self.cur.execute(query, (self.selected_item, rowid[0]))
                self.conn.commit()

                self.food_table.removeRow(self.selected_row)
                del self.selected_row


    def moveRowToFoodTable(self):
        selected_row = self.goodFood.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Seçim Hatası", "Lütfen önce bir satır seçin.")
            return
        selected_item = self.goodFood.item(selected_row, 0).text()

        row_position = self.food_table.rowCount()
        self.food_table.insertRow(row_position)
        self.food_table.setItem(row_position, 0, QTableWidgetItem(selected_item))
        
        query = "UPDATE GoodFood SET FoodItem = NULL WHERE Username = ? AND FoodItem = ?"
        self.cur.execute(query, (self.username, selected_item))
        self.conn.commit()        
        
    
        self.goodFood.removeRow(selected_row)

    def exitFromPage(self):
        self.close()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()


if __name__ =="__main__":
    app = QApplication(sys.argv)
    ui=FirstPage()
    ui.show()
    app.exec_()
       
