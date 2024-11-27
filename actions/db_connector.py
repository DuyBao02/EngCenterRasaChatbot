import mysql.connector
import logging

# Cấu hình logging level và format cho các thông điệp log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sử dụng logging trong code của bạn
logging.info('This is an information message.')
logging.warning('This is a warning message.')
logging.error('This is an error message.')


class DatabaseConnector:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            logging.info("Connected to database successfully.")
        except mysql.connector.Error as err:
            logging.error(f"Error occurred while connecting to database: {err}")

    def execute_query(self, query, params=None, commit=False, fetchone=False):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if commit:
                self.connection.commit()  # Chỉ commit khi thực hiện các truy vấn thay đổi dữ liệu
                return True
            elif fetchone:
                result = self.cursor.fetchone()  # Lấy kết quả cho một truy vấn SELECT và trả về một bản ghi
                return result
            else:
                result = self.cursor.fetchall()  # Lấy kết quả cho các truy vấn SELECT và trả về một danh sách kết quả
                return result
        except mysql.connector.Error as err:
            logging.error(f"Error occurred while executing query: {err}")
            if commit:
                self.connection.rollback()  # Rollback nếu có lỗi xảy ra trong truy vấn thay đổi dữ liệu
            return False

    def close(self):
        try:
            self.cursor.close()
            self.connection.close()
            logging.info("Connection closed.")
        except mysql.connector.Error as err:
            logging.error(f"Error occurred while closing connection: {err}")

