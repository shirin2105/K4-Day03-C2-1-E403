"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, parse_cv, sanitize_cv_input, score_candidate, check_job_requirements, search_calendar_availability, schedule_interview, send_email_notification, query_candidate_database, generate_interview_questions
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) HOÀN CHỈNH.
    LLM tự động suy luận, gọi Tool thực tế và tự dừng khi có Final Answer.
    """
    import re
    import json
    
    # 🛡️ SANITIZE USER INPUT: Vô hiệu hóa nhãn giả mạo system directive
    sanitized_query = re.sub(r'\[SYSTEM\s+DIRECTIVE.*?\]', '[USER_DATA_REDACTED]', user_query, flags=re.IGNORECASE)
    sanitized_query = re.sub(r'DAN\s+Mode\s+Activated', '[UNAUTHORIZED_ROLEPLAY]', sanitized_query, flags=re.IGNORECASE)
    
    # Context Buffer: Nơi lưu trữ toàn bộ lịch sử Suy nghĩ - Hành động - Kết quả
    context = f"Question: {sanitized_query}\n"
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # 1. Gọi LLM dự đoán bước tiếp theo dựa trên ngữ cảnh hiện tại
        response = provider.generate(context, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"{response.strip()}") 
        
        # Lưu câu trả lời của LLM vào bộ nhớ
        context += response.strip() + "\n"
        
        # 2. KIỂM TRA ĐIỀU KIỆN DỪNG
        if "Final Answer:" in response:
            print("🏁 [THÀNH CÔNG] Agent đã thu thập đủ thông tin và đưa ra câu trả lời cuối!")
            break
            
        # 3. PHÂN TÍCH HÀNH ĐỘNG (Parse Action)
        # Bắt chuỗi có dạng "Action: ten_tool[tham so 1, tham so 2]"
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response) 
        
        if action_match:
            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()
            
            # Tách các tham số (bỏ khoảng trắng và dấu nháy thừa)
            args_list = [arg.strip(" '\"") for arg in raw_args.split(",")]
            obs = ""
            
            # 🛠️ VIBE CODE ROLE 4: Adapter xử lý "lệch pha" giữa Role 2 và Role 3
            try:
                if tool_name == "search_candidate":
                    # Role 3 gọi search_candidate, nhưng Role 2 viết query_candidate_database(JSON)
                    name = args_list[0] if len(args_list) > 0 else ""
                    query_json = json.dumps({"action": "get", "candidate_name": name}, ensure_ascii=False)
                    obs = AVAILABLE_TOOLS["query_candidate_database"](query_json)
                    
                elif tool_name == "schedule_interview":
                    # Role 3 gọi 2 tham số (name, time), Role 2 lại yêu cầu 3 tham số (thêm interviewer)
                    name = args_list[0] if len(args_list) > 0 else ""
                    time_slot = args_list[1] if len(args_list) > 1 else ""
                    interviewer = "hr_bot@company.com" # Role 4 tự hardcode cứu nguy
                    obs = AVAILABLE_TOOLS["schedule_interview"](name, interviewer, time_slot)
                    
                elif tool_name in AVAILABLE_TOOLS:
                    obs = AVAILABLE_TOOLS[tool_name](*args_list)
                else:
                    obs = f"Lỗi: Tool '{tool_name}' không khả dụng trong hệ thống."
                    
            except Exception as e:
                obs = f"Lỗi hệ thống khi chạy tool: {str(e)}"
            
            print(f"👁️ Observation: {obs}")
            # Đưa kết quả (Observation) trở lại vào Context để LLM đọc ở vòng lặp sau
            context += f"Observation: {obs}\n"
            
        else:
            # LLM "ảo giác" quên format -> Trả Observation nhắc nhở
            warning = "Lỗi format: Hãy xuất ra định dạng Action: tên_tool[tham_số] hoặc Final Answer: <câu trả lời>."
            print(f"⚠️ {warning}")
            context += f"Observation: {warning}\n"
            
    # 4. KIỂM TRA PHANH AN TOÀN (GUARDRAIL)
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Vượt quá {MAX_ITERATIONS} vòng lặp. Ngắt Agent an toàn!")


def interactive_mode(provider):
    print("\n==================================================")
    print("💬 CHẾ ĐỘ TƯƠNG TÁC TRỰC TIẾP (INTERACTIVE AGENT CHAT)")
    print("Gõ câu hỏi của bạn để thử nghiệm ReAct Agent (Gõ 'exit' hoặc 'quit' để thoát)")
    print("==================================================")
    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Cảm ơn bạn đã thử nghiệm AI Agent!")
                break
            run_react_agent(user_input, provider)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã thoát ứng dụng.")
            break


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # 1. Chạy thử câu test số 3 (Multi-step)
    sample_query_3 = tests[2]["question"]
    print("--- DEMO 1: CHẠY CÂU TEST #3 TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query_3, provider)
    
    print("\n--- DEMO 2: CHẠY CÂU TEST #3 TRÊN REACT AGENT ---")
    run_react_agent(sample_query_3, provider)

    # 2. Role 1 kiểm tra câu test số 4 & 5 (Edge Case & Guardrail Safety)
    print("\n==================================================")
    print("🛡️ ROLE 1 KIỂM TRỬA PHANH GUARDRAIL (EDGE CASE & SAFETY)")
    print("==================================================")
    
    sample_query_4 = tests[3]["question"]
    print(f"\n--- DEMO 3: CÂU BẪY DỮ LIỆU (TEST CASE #4) ---")
    run_react_agent(sample_query_4, provider)

    sample_query_5 = tests[4]["question"]
    print(f"\n--- DEMO 4: CÂU BẪY PROMPT INJECTION (TEST CASE #5) ---")
    run_react_agent(sample_query_5, provider)

    # 3. Mở Chế độ Tương tác Trực tiếp cho Người dùng Test
    interactive_mode(provider)
