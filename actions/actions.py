from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .db_connector import DatabaseConnector
import logging, time, smtplib, bcrypt, jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rasa_sdk.events import SlotSet
from .tts_action.tts_action import speak_vietnamese
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class action_default_fallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Xin lỗi, tôi không hiểu bạn muốn nói gì. Bạn có thể nói lại một cách rõ ràng hơn được không?"
        dispatcher.utter_message(text=text)
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_default_fallback' thực thi trong {execution_time} giây")
        return []
    
class action_query_teachers(Action):
    def name(self) -> Text:
        return "action_query_teachers"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()

        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )

        teachers_data = db_connector.execute_query("SELECT * FROM users WHERE role = 'Teacher'")
        buttons = []

        for user in teachers_data:
            teacher_id = str(user[0])
            buttons.append({"title": user[1], "payload": f"/choose_teacher{{\"teacher_id\":\"{teacher_id}\"}}"})

        db_connector.close()

        text = "Dưới đây là những giảng viên đang giảng dạy ở Trung tâm. Bạn có thể chọn giáo viên để xem thông tin:"
        dispatcher.utter_message(text=text, buttons=buttons)
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_query_teachers' thực thi trong {execution_time} giây")

        return []
    
class action_get_link_teachers(Action):
    def name(self) -> Text:
        return "action_get_link_teachers"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()
        
        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )
        
        teacher_id = tracker.get_slot("teacher_id")

        teachers_name_data = db_connector.execute_query(
            "SELECT name FROM users WHERE id = %s",
            (teacher_id,),
            commit=False  # Đặt commit=False hoặc bỏ qua tham số này cho truy vấn SELECT
        )

        if teacher_id:
            for teachers_name in teachers_name_data:
                name = teachers_name[0]
                dispatcher.utter_message(text=f"Đây là đường dẫn đến trang của {name}: http://localhost:8001/teachers/{teacher_id}")
                text = "Đây là đường dẫn đến trang của giảng viên bạn đã chọn, nhấp vào để xem thử nhé!"
                speak_vietnamese(text)
        else:
            text = "Không có thông tin về giáo viên được chọn."
            dispatcher.utter_message(text=text)
            speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_get_link_teachers' thực thi trong {execution_time} giây")

        return []

class action_query_courses(Action):
    def name(self) -> Text:
        return "action_query_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()

        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )

        courses_data = db_connector.execute_query("SELECT id_3course, name_course FROM thirdcourses WHERE JSON_LENGTH(students_list) < maxStudents")
        buttons = []

        for course in courses_data:
            course_id = str(course[0])
            buttons.append({"title": course[1], "payload": f"/choose_courseid_to_register{{\"course_id\":\"{course_id}\"}}"})

        db_connector.close()

        text = "Các khóa học ở trung tâm sẽ được mở thường xuyên, bạn có thể truy cập vào đường dẫn để kiểm tra xem có những khóa học nào được mở tại đây: _http://localhost:8001/currentcourses_ \nDựa trên các thông tin của khoá học như thời gian học, phòng học, số lượng học viên, học phí giảng viên phụ trách.\nDưới đây là danh sách khóa học bạn có thể đăng ký:"
        dispatcher.utter_message(text=text, buttons=buttons)
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_query_courses' thực thi trong {execution_time} giây")

        return []
    
class action_collect_infor(Action):
    def name(self) -> Text:
        return "action_collect_infor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()
        
        course_id = tracker.get_slot("course_id")

        if course_id:
            dispatcher.utter_message(template="utter_ask_email")
            text = "1. Để đăng ký khóa học, bạn cần thực hiện các bước sau, đầu tiên hãy nhập email để chúng tôi biết bạn là ai? Nếu chưa có tài khoản thành viên, hãy vào \n_http://localhost:8001/register_ để thực hiện việc đăng ký!"
            speak_vietnamese(text)
            return [SlotSet("course_id", course_id)]
        
        else:
            text = "Không có thông tin về khóa học được chọn. Vui lòng thử lại sau!"
            dispatcher.utter_message(text=text)
            speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_collect_infor' thực thi trong {execution_time} giây")

        return []
    
class action_ask_password_register_course(Action):
    def name(self) -> Text:
        return "action_ask_password_register_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()
        
        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )
        
        course_id = tracker.get_slot("course_id")
        email = tracker.get_slot('email')

        if not email:
            text = "Bạn chưa nhập email. Vui lòng nhập lại."
            dispatcher.utter_message(text=text)
            speak_vietnamese(text)
            execution_time = round((time.time() - start_time), 5)
            logger.info(f"Action 'action_ask_password_register_course' thực thi trong {execution_time} giây với lỗi chưa có email")
            return [SlotSet("course_id", course_id)]

        print("------------------------------------------")
        print(course_id)
        print(email)
        print("------------------------------------------")

        # Kiểm tra email với vai trò Student có tồn tại trong database hay không
        email_data = db_connector.execute_query(
            "SELECT email FROM users WHERE email = %s AND role = 'Student'",
            (email,),
            commit=False
        )

        if not email_data:
            dispatcher.utter_message(text=f"Email _{email}_ không tồn tại hoặc _{email}_ không phải là học viên. Vui lòng thử lại.")
            text = "Email không tồn tại hoặc email này không phải là học viên. Vui lòng thử lại."
            speak_vietnamese(text)
            execution_time = round((time.time() - start_time), 5)
            logger.info(f"Action 'action_ask_password_register_course' thực thi trong {execution_time} giây")
            return [SlotSet("course_id", course_id)]

        else:
            dispatcher.utter_message(template="utter_ask_password")
            text = "2. Có email thì phải có mật khẩu đúng không? Hãy nhập mật khẩu mà bạn đã đăng ký với email bạn cung cấp ở trên nhé!"
            speak_vietnamese(text)
            execution_time = round((time.time() - start_time), 5)
            logger.info(f"Action 'action_ask_password_register_course' thực thi trong {execution_time} giây")
            return [SlotSet("course_id", course_id), SlotSet("email", email)]


class action_ask_verify_mail_register_course(Action):
    def name(self) -> Text:
        return "action_ask_verify_mail_register_course"
    
    def send_email(self, sender, receiver, subject, body):
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
            server.starttls()
            server.login("d2290debe15dc3", "09f3670b4754cb")
            server.sendmail(sender, receiver, message.as_string())

    def generate_verification_token(self, email, course_id):
        SECRET_KEY = "15db20english02center"  # Đặt một khóa bí mật an toàn
        expiration_date = datetime.now() + timedelta(hours=1)  # Token hết hạn sau 1 giờ
        token_payload = {'email': email, 'course_id': course_id, 'exp': expiration_date}
        token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
        return token

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        start_time = time.time()
        
        db_connector = DatabaseConnector(
            host="127.0.0.1",
            user="root",
            password="",
            database="dbec"
        )

        course_id = tracker.get_slot("course_id")
        email = tracker.get_slot('email')
        password = tracker.get_slot('password')

        password_data = db_connector.execute_query(
            "SELECT password FROM users WHERE email = %s",
            (email,),
            commit=False
        )

        if password_data:
            hashed_password = password_data[0][0]  # Truy cập vào phần tử đầu tiên của tuple, sau đó truy cập vào giá trị của cột "password"
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                dispatcher.utter_message(text=f"Mật khẩu khớp với {email}. Quá trình đăng ký khóa học đang được tiếp tục.")
                text = "Mật khẩu khớp với email. Quá trình đăng ký khóa học đang được tiếp tục."
                speak_vietnamese(text)
            else:
                dispatcher.utter_message(text=f"Mật khẩu không khớp với {email}. Vui lòng thử lại.")
                text = "Mật khẩu không khớp với email. Vui lòng thử lại."
                speak_vietnamese(text)
                execution_time = round((time.time() - start_time), 5)
                logger.info(f"Action 'action_ask_verify_mail_register_course' thực thi trong {execution_time} giây và có lỗi thực thi với mật khẩu")
                return []
            
        token = self.generate_verification_token(email, course_id)
        # Lưu token vào cơ sở dữ liệu
        db_connector.execute_query(
            "INSERT INTO verified_token_register_course (token, flag) VALUES (%s, %s)",
            (token, 0),
            commit=True
        )

        verification_link = f"http://localhost:3000/chatbot/verify_email?token={token}"

        # Gửi email xác thực
        sender = "DB English Center <dbec@gmail.com>"
        receiver = email
        subject = "Verify Email Address from DBEC"
        body  = f"""\
        <html>
            <body>
                <p>Xin chào, {email}<br>
                Vui lòng nhấp vào liên kết dưới đây để xác thực địa chỉ email của bạn:<br>
                <a href="{verification_link}">Xác thực Email</a><br>
                Mã xác thực này sẽ hết hạn trong 1 giờ</br>
                Nếu bạn không thực hiện việc đăng ký này, vui lòng bỏ qua mail này.<br>
                Trung tâm DBEC trân trọng.
                </p>
            </body>
        </html>
        """

        self.send_email(sender, receiver, subject, body)

        text = "3. Cuối cùng vì lý do bảo mật, có một email xác thực đã gửi đến email của bạn, vui lòng nhập nó để hoàn thành việc đăng ký khóa học."
        dispatcher.utter_message(template="utter_ask_verify_email")
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_ask_verify_mail_register_course' thực thi trong {execution_time} giây")
        
        return []

class action_utter_speak_chao_hoi(Action):
    def name(self) -> Text:
        return "action_utter_speak_chao_hoi"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Xin chào, tôi là chát bót hỗ trợ tiếng việt về các vấn đề của Trung tâm Tiếng Anh đi bi i si, sau đây là những thông tin bạn có thể tìm hiểu, rất hân hạnh được giúp bạn!"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_chao_hoi' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_thoi_gian(Action):
    def name(self) -> Text:
        return "action_utter_speak_thoi_gian"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Trung tâm đi bi i si bắt đầu mở cửa hoạt động từ 7h30, đến 21h30 sẽ đóng cửa trừ ngày lễ và Chủ nhật. Nếu bạn có vấn đề gì hãy đến vào thời gian này. Chúng tôi rất hoan nghênh bạn!"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_thoi_gian' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_dia_chi(Action):
    def name(self) -> Text:
        return "action_utter_speak_dia_chi"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Địa chỉ của Trung tâm tại trường công nghệ thông tin và truyền thông, thuộc trường đại học cần thơ khu hai. Đường ba tháng hai, Xuân Khánh, Ninh Kiều, Cần Thơ. Cách thức liên lạc thì bạn có thể xem tại trang này nhé"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_dia_chi' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_chuc_nang(Action):
    def name(self) -> Text:
        return "action_utter_speak_chuc_nang"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Những điều mà tôi có thể giúp bạn là trả lời những câu hỏi liên quan đến trung tâm. Hơn thế thì tôi cũng sẽ giúp bạn đăng ký khóa học cho học viên luôn đấy nhé!"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_chuc_nang' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_cam_on(Action):
    def name(self) -> Text:
        return "action_utter_speak_cam_on"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Không có gì đâu, vấn đề của bạn là vấn đề của tôi!"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_cam_on' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_ask_create_account(Action):
    def name(self) -> Text:
        return "action_utter_speak_ask_create_account"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Rất tiếc nhưng quá trình để tôi có thể đăng ký tài khoản giúp bạn vẫn đang được phát triển, đợi tôi nhé!"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_ask_create_account' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_no_account(Action):
    def name(self) -> Text:
        return "action_utter_speak_no_account"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Nếu bạn chưa có tài khoản. Hãy truy cập vào đường link sau .Sau khi có tài khoản, bạn có thể đăng ký khóa học rồi đó! Hoặc tôi cũng có thể giúp bạn đăng ký khóa học"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_no_account' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_tam_biet(Action):
    def name(self) -> Text:
        return "action_utter_speak_tam_biet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Chúc bạn có một ngày tốt lành <3 to bự"
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_tam_biet' thực thi trong {execution_time} giây")
        return []

class action_utter_speak_iamabot(Action):
    def name(self) -> Text:
        return "action_utter_speak_iamabot"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        start_time = time.time()

        text = "Tôi là chát bót tiếng việt hỗ trợ và giúp bạn tìm hiểu về Trung tâm Tiếng Anh đi bi i si."
        speak_vietnamese(text)

        execution_time = round((time.time() - start_time), 5)
        logger.info(f"Action 'action_utter_speak_iamabot' thực thi trong {execution_time} giây")
        return []
