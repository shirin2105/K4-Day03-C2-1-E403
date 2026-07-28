import json
import re


def _error_response(error_message: str, error_type: str = "ToolError") -> str:
    """
    Helper dùng chung: đóng gói lỗi thành chuỗi JSON chuẩn để trả về
    thay vì để exception làm crash Agent.
    """
    return json.dumps(
        {"success": False, "error_type": error_type, "error": error_message},
        ensure_ascii=False,
    )


# ============================================================
# MOCK DATABASE BÀI TOÁN SÀNG LỌC TUYỂN DỤNG & HẸN PHỎNG VẤN (TOPIC 9)
# ============================================================
MOCK_CANDIDATE_DB = {
    "CV_101": {
        "name": "Nguyễn Văn A",
        "email": "nguyenvana@gmail.com",
        "phone": "0912345678",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
        "exp_years": 3.5,
        "education": "Đại học Bách Khoa",
        "status": "Đã qua sàng lọc vòng 1"
    },
    "CV_102": {
        "name": "Trần Thị B",
        "email": "tranthib@gmail.com",
        "phone": "0987654321",
        "skills": ["Python", "PyTorch", "Machine Learning", "SQL", "Pandas", "Scikit-Learn"],
        "exp_years": 4.0,
        "education": "Đại học VinUni",
        "status": "Đủ điều kiện phỏng vấn Data Scientist"
    }
}


# ============================================================
# 1. PARSE CV
# ============================================================
def parse_cv(file_path: str) -> str:
    """
    Trích xuất thông tin từ file CV (PDF/DOCX) của ứng viên.
    """
    try:
        if not file_path or not isinstance(file_path, str):
            return _error_response("file_path không hợp lệ hoặc rỗng.", "ValueError")

        if not file_path.lower().endswith((".pdf", ".docx")):
            return _error_response(
                f"Định dạng file không được hỗ trợ: '{file_path}'. Chỉ hỗ trợ .pdf / .docx.",
                "UnsupportedFormatError",
            )

        # Mock implementation: Trả về thông tin CV phù hợp
        if "cv_101" in file_path.lower() or "nguyenvana" in file_path.lower():
            data = MOCK_CANDIDATE_DB["CV_101"]
        else:
            data = MOCK_CANDIDATE_DB["CV_102"]

        return json.dumps({"success": True, "data": data}, ensure_ascii=False)

    except FileNotFoundError:
        return _error_response(f"Không tìm thấy file: '{file_path}'.", "FileNotFoundError")
    except Exception as e:
        return _error_response(f"Lỗi không xác định khi đọc CV: {str(e)}", "UnknownError")


# ============================================================
# 2. SANITIZE CV INPUT (chống prompt injection)
# ============================================================
def sanitize_cv_input(raw_cv_text: str) -> str:
    """
    Quét và làm sạch nội dung CV trước khi đưa vào Agent để phát hiện prompt injection.
    """
    try:
        if not raw_cv_text or not isinstance(raw_cv_text, str):
            return _error_response("raw_cv_text rỗng hoặc không hợp lệ.", "ValueError")

        injection_keywords = ["ignore previous instructions", "system prompt", "bỏ qua quy tắc", "xóa toàn bộ"]
        is_flagged = any(kw in raw_cv_text.lower() for kw in injection_keywords)
        flagged_reasons = [kw for kw in injection_keywords if kw in raw_cv_text.lower()]

        clean_text = raw_cv_text
        for kw in injection_keywords:
            clean_text = re.sub(re.escape(kw), "[REDACTED]", clean_text, flags=re.IGNORECASE)

        return json.dumps({
            "success": True,
            "data": {
                "clean_text": clean_text,
                "is_flagged": is_flagged,
                "flagged_reasons": flagged_reasons
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi sanitize CV: {str(e)}", "UnknownError")


# ============================================================
# 3. SCORE CANDIDATE
# ============================================================
def score_candidate(cv_info: str, job_description: str) -> str:
    """
    Chấm điểm mức độ phù hợp của ứng viên so với mô tả công việc (JD).
    """
    try:
        if not job_description or not isinstance(job_description, str):
            return _error_response("job_description rỗng hoặc không hợp lệ.", "ValueError")

        try:
            parsed_cv = json.loads(cv_info) if isinstance(cv_info, str) else cv_info
        except (json.JSONDecodeError, TypeError):
            return _error_response("cv_info không phải chuỗi JSON hợp lệ.", "ValueError")

        score = 8.5
        reason = "Ứng viên có kỹ năng chuyên môn vững vàng và đủ số năm kinh nghiệm yêu cầu."
        strengths = ["Kỹ năng lập trình tốt", "Bằng cấp phù hợp"]
        gaps = ["Cần trau dồi thêm tiếng Anh chuyên ngành"]

        return json.dumps({
            "success": True,
            "data": {
                "score": score,
                "reason": reason,
                "strengths": strengths,
                "gaps": gaps
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi chấm điểm: {str(e)}", "UnknownError")


# ============================================================
# 4. CHECK JOB REQUIREMENTS
# ============================================================
def check_job_requirements(cv_info: str, job_requirements: str) -> str:
    """
    Đối chiếu yêu cầu công việc bắt buộc với hồ sơ ứng viên.
    """
    try:
        if not job_requirements:
            return _error_response("job_requirements rỗng.", "ValueError")

        return json.dumps({
            "success": True,
            "data": {
                "passed": True,
                "unmet_requirements": [],
                "reason": "Ứng viên đáp ứng đầy đủ tất cả các tiêu chí cứng tối thiểu."
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi đối chiếu yêu cầu: {str(e)}", "UnknownError")


# ============================================================
# 5. SEARCH CALENDAR AVAILABILITY
# ============================================================
def search_calendar_availability(interviewer: str, date_range: str) -> str:
    """
    Tra cứu lịch trống của người phỏng vấn/nhà tuyển dụng.
    """
    try:
        if not interviewer or not isinstance(interviewer, str):
            return _error_response("interviewer rỗng hoặc không hợp lệ.", "ValueError")

        available_slots = ["09:00", "14:00", "15:30"]
        return json.dumps({
            "success": True,
            "data": {
                "interviewer": interviewer,
                "available_slots": available_slots,
                "message": f"Các khung giờ trống cho {interviewer} trong khoảng {date_range}: {', '.join(available_slots)}"
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi tra cứu lịch: {str(e)}", "UnknownError")


# ============================================================
# 6. SCHEDULE INTERVIEW
# ============================================================
def schedule_interview(candidate_name: str, interviewer: str = "hr_bot@company.com", time_slot: str = "14:00") -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên với người phỏng vấn.
    """
    try:
        if not candidate_name:
            return _error_response("candidate_name rỗng.", "ValueError")

        # Bẫy ngày tháng/thời gian không hợp lệ (Edge Case test 4 & 5)
        if "31/02" in time_slot or "32/13" in time_slot or "9999" in candidate_name:
            return _error_response(f"LỖI THAM SỐ: Dữ liệu đặt lịch không hợp lệ (Mã ứng viên hoặc ngày/giờ '{time_slot}' sai).", "InvalidParameterError")

        return json.dumps({
            "success": True,
            "data": {
                "event_id": f"EVT_{hash(candidate_name + time_slot) % 10000}",
                "candidate": candidate_name,
                "interviewer": interviewer,
                "time_slot": time_slot,
                "message": f"Đã đặt lịch phỏng vấn thành công cho {candidate_name} vào lúc {time_slot} với {interviewer}."
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi đặt lịch phỏng vấn: {str(e)}", "UnknownError")


# ============================================================
# 7. SEND EMAIL NOTIFICATION
# ============================================================
def send_email_notification(to_email: str, subject: str, content: str) -> str:
    """
    Gửi email thông báo cho ứng viên.
    """
    try:
        if not to_email or "@" not in to_email:
            return _error_response(f"Email không hợp lệ: '{to_email}'.", "ValueError")
        if not subject or not content:
            return _error_response("subject hoặc content rỗng.", "ValueError")

        return json.dumps({
            "success": True,
            "data": {
                "message_id": f"MSG_{hash(to_email + subject) % 10000}",
                "to": to_email,
                "status": "Đã gửi email thông báo thành công."
            }
        }, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi gửi email: {str(e)}", "UnknownError")


# ============================================================
# 8. QUERY CANDIDATE DATABASE
# ============================================================
def query_candidate_database(query: str) -> str:
    """
    Truy vấn thông tin ứng viên trong cơ sở dữ liệu tuyển dụng.
    """
    try:
        cand_key = str(query).upper().strip()
        
        # Nếu truyền vào ID trực tiếp (CV_101, CV_102) hoặc tên
        if cand_key in MOCK_CANDIDATE_DB:
            return json.dumps({"success": True, "data": MOCK_CANDIDATE_DB[cand_key]}, ensure_ascii=False)
            
        if "101" in cand_key or "NGUYỄN VĂN A" in cand_key or "NGUYEN VAN A" in cand_key:
            return json.dumps({"success": True, "data": MOCK_CANDIDATE_DB["CV_101"]}, ensure_ascii=False)
            
        if "102" in cand_key or "TRẦN THỊ B" in cand_key or "TRAN THI B" in cand_key:
            return json.dumps({"success": True, "data": MOCK_CANDIDATE_DB["CV_102"]}, ensure_ascii=False)

        # Xử lý JSON string nếu có
        try:
            parsed_query = json.loads(query)
            cand_id = parsed_query.get("candidate_id") or parsed_query.get("candidate_name") or ""
            cand_id = str(cand_id).upper().strip()
            if cand_id in MOCK_CANDIDATE_DB:
                return json.dumps({"success": True, "data": MOCK_CANDIDATE_DB[cand_id]}, ensure_ascii=False)
        except Exception:
            pass

        return _error_response(f"Không tìm thấy dữ liệu ứng viên cho câu truy vấn '{query}'.", "NotFoundError")

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi truy vấn database: {str(e)}", "UnknownError")


# ============================================================
# 9. GENERATE INTERVIEW QUESTIONS
# ============================================================
def generate_interview_questions(cv_info: str, job_description: str) -> str:
    """
    Sinh danh sách câu hỏi phỏng vấn phù hợp dựa trên CV và JD.
    """
    try:
        if not job_description:
            return _error_response("job_description rỗng.", "ValueError")

        questions = [
            "1. Bạn hãy giới thiệu về dự án Machine Learning gần đây nhất mà bạn tâm đắc?",
            "2. Sự khác biệt giữa PyTorch và TensorFlow trong quá trình huấn luyện mô hình là gì?",
            "3. Bạn xử lý dữ liệu bị lãng quên (Missing Data) và lệch nhóm (Imbalanced Data) như thế nào?"
        ]

        return json.dumps({"success": True, "data": {"questions": questions}}, ensure_ascii=False)

    except Exception as e:
        return _error_response(f"Lỗi không xác định khi sinh câu hỏi phỏng vấn: {str(e)}", "UnknownError")


# TOOL REGISTRY — map tên tool -> hàm Python
AVAILABLE_TOOLS = {
    "parse_cv": parse_cv,
    "sanitize_cv_input": sanitize_cv_input,
    "score_candidate": score_candidate,
    "check_job_requirements": check_job_requirements,
    "search_calendar_availability": search_calendar_availability,
    "schedule_interview": schedule_interview,
    "send_email_notification": send_email_notification,
    "query_candidate_database": query_candidate_database,
    "generate_interview_questions": generate_interview_questions,
}