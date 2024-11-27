from flask import Flask, request, jsonify, render_template
import requests, jwt, json
from actions.db_connector import DatabaseConnector
from datetime import datetime

RASA_API_URL = 'http://localhost:5005/webhooks/rest/webhook'

app = Flask(__name__)

def check_token_used(token):
    # Kết nối với cơ sở dữ liệu
    db_connector = DatabaseConnector(
        host="127.0.0.1",
        user="root",
        password="",
        database="dbec"
    )

    result = db_connector.execute_query(
        "SELECT flag FROM verified_token_register_course WHERE token = %s",
        (token,),
        commit=False
    )
    if result:
        return result[0][0] == 1  # Trả về True nếu token đã được sử dụng
    return False  # Trả về False nếu token chưa được sử dụng hoặc không tồn tại

def mark_token_as_used(token):
    # Kết nối với cơ sở dữ liệu
    db_connector = DatabaseConnector(
        host="127.0.0.1",
        user="root",
        password="",
        database="dbec"
    )

    db_connector.execute_query(
        "UPDATE verified_token_register_course SET flag = 1 WHERE token = %s",
        (token,),
        commit=True
    )

@app.route("/chatbot/verify_email")
def verify_email():
    token = request.args.get('token')
    if not token:
        return "Không tìm thấy Token!", 400

    if check_token_used(token):
        return "Việc đăng ký khóa học đã hoàn tất, do bạn đã xác thực mail rồi nên bạn không thể xác thực nữa!", 400
    
    try:
        SECRET_KEY = "15db20english02center"
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        email = payload['email']
        course_id = payload['course_id']
        
        # Kết nối với cơ sở dữ liệu
        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )

        # Tìm id của người dùng dựa trên email
        user_id = db_connector.execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,),
            commit=False
        )
        if not user_id:
            return "Người dùng không tồn tại!", 400

        user_id = user_id[0][0]

        # Lấy danh sách học viên và số lượng tối đa của khóa học dựa trên course_id
        course3_info = db_connector.execute_query(
            "SELECT students_list FROM thirdcourses WHERE id_3course = %s",
            (course_id,),
            commit=False
        )
        if not course3_info:
            return "Không thể tìm thấy thông tin về khóa học!", 400

        student_list_str = course3_info[0][0]

        # Chuyển đổi student_list từ chuỗi sang danh sách
        if student_list_str:
            student_list = student_list_str.strip('[]').split(',')  # Chuyển chuỗi thành danh sách dựa trên dấu phẩy
            student_list = [int(id) for id in student_list]  # Chuyển đổi mỗi phần tử thành số nguyên
        else:
            student_list = []
        
        student_list.append(user_id)
        
        # Chuyển đổi danh sách học viên trở lại thành chuỗi để lưu vào cơ sở dữ liệu
        student_list_str = str(student_list)
        
        # Cập nhật danh sách học viên trong bảng thirdcourses
        db_connector.execute_query(
            "UPDATE thirdcourses SET students_list = %s WHERE id_3course = %s",
            (student_list_str, course_id),
            commit=True
        )

        # Cập nhật cột students_list trong bảng courses
        db_connector.execute_query(
            "UPDATE courses SET students_list = %s WHERE id_course = %s",
            (student_list_str, course_id),
            commit=True
        )

        #Tạo biên lai thanh toán
        # Lấy thông tin học phí của khóa học
        course_fee_info = db_connector.execute_query(
            "SELECT tuitionFee FROM courses WHERE id_course = %s",
            (course_id,),
            commit=False
        )
        if not course_fee_info:
            return "Không thể tìm thấy thông tin học phí của khóa học!", 400

        course_fee = course_fee_info[0][0]

        name_bill_list = [course_id]
        name_bill_str = json.dumps(name_bill_list).replace('"', r'\"')
        final_name_bill = f'"{name_bill_str}"'
        # print(final_name_bill)  # Kết quả: "[\"TF_2804\"]"

        db_connector.execute_query(
            "INSERT INTO bills (user_id, name_bill, tuitionFee, is_paid, created_at, updated_at) VALUES (%s, %s, %s, FALSE, NOW(), NOW())",
            (user_id, final_name_bill, course_fee),
            commit=True
        )

        mark_token_as_used(token)
        return "Email đã được xác thực thành công và đã được thêm vào danh sách học viên!"
    except jwt.ExpiredSignatureError:
        return "Đường link xác minh đã hết hạn kết nối!", 400
    except jwt.InvalidTokenError:
        return "Mã xác thực không hợp lệ!", 400

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, port=3000)


# @app.route("/")
# def index():
#     return render_template('index.html')

# @app.route("/chatbot/verify_email")
# def verify_email():
#     token = request.args.get('token')
#     if not token:
#         return "Token is missing!", 400
    
#     try:
#         SECRET_KEY = "15db20english02center"
#         payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
#         email = payload['email']
        
#         # Kết nối với cơ sở dữ liệu và cập nhật trạng thái xác thực
#         db_connector = DatabaseConnector(
#             host="127.0.0.1",
#             user="root",
#             password="",
#             database="dbec"
#         )
        
#         current_time = datetime.now()
#         db_connector.execute_query(
#             "UPDATE persons SET email_verified_at = %s WHERE email = %s",
#             (current_time, email),
#             commit=True
#         )
        
#         # Gửi thông báo thành công
#         return "Email đã được xác thực thành công!"
#     except jwt.ExpiredSignatureError:
#         return "Đường link xác minh đã hết hạn kết nối!", 400
#     except jwt.InvalidTokenError:
#         return "Mã xác thực không hợp lệ!", 400

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     user_message = request.json['message']
#     print("User Message:", user_message)
#
#     rasa_response = requests.post(RASA_API_URL, json={'message': user_message})
#     rasa_response_json = rasa_response.json()
#
#     print("Rasa Response:", rasa_response_json)
#     bot_response = rasa_response_json[0]['text'] if rasa_response_json else 'Sorry, I did not understand that'
#     return jsonify({'response': bot_response})
