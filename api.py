import os

def get_ai_response(user_input, course_code):
    return f"Hello, I am your AI tutor of {course_code}. I am still learning. not implemented yet."

def check_course_exists(course_path):
    return os.path.exists(course_path)

def get_all_courses(directory):
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
