import streamlit as st
import os
import json
from api import check_course_exists, get_all_courses
from model import get_agent


def add_custom_css():
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] button  {
            width: 100% !important; 
            height: 50px !important; 
            margin-bottom: 5px !important; 
        }
        </style>
        """, unsafe_allow_html=True)


@st.cache_resource
def create_course_agent(course_code):
    course_path = os.path.join('document', course_code)

    with open(os.path.join(course_path, 'config.json'), 'r') as json_file:
        course_config = json.load(json_file)
        file_categories = {
            'slides': course_config['uploaded_files'].get('slides', []),
            'assignments': course_config['uploaded_files'].get('assignments', []),
            'syllabus': course_config['uploaded_files'].get('syllabus', [])
        }
        print(file_categories['slides'])
        print(file_categories['assignments'])
        print(file_categories['syllabus'])
        system_prompt = course_config['system_prompt'] if 'system_prompt' in course_config else ''
        agent = get_agent(
            [os.path.join('document', course_code, file)
             for file in file_categories['slides']],
            [os.path.join('document', course_code, file)
             for file in file_categories['assignments']],
            [os.path.join('document', course_code, file)
             for file in file_categories['syllabus']],
            os.path.join('db', f'{course_code}_slides_index'),
            os.path.join('db', f'{course_code}_homework_index'),
            os.path.join('db', f'{course_code}_syllabus_index'),
            course_code=course_code,
            course_title=course_config['course_description'],
            instructor_prompt=system_prompt,
        )
        return agent


def get_ai_response(user_input, course_code):
    if f'agent_{course_code}' not in st.session_state:
        with st.spinner("Creating AI Tutor..."):
            agent = create_course_agent(course_code)
        st.session_state[f'agent_{course_code}'] = agent
    current_agent = st.session_state[f'agent_{course_code}']
    resp = None
    with st.spinner("Thinking..."):
        resp = current_agent.chat(user_input)
    return resp


def show_update_course_form(course_code):
    st.title(f"Update Course: {course_code}")
    course_path = os.path.join('document', course_code)
    with open(os.path.join(course_path, 'config.json'), 'r') as json_file:
        course_config = json.load(json_file)

    st.subheader("Existing Files")
    for category, files in course_config['uploaded_files'].items():
        st.markdown(f"**{category.title()}**")
        for file in files:
            col1, col2 = st.columns([0.8, 0.2])
            col1.markdown(file)
            if col2.button(f"Delete {file}", key=f"delete_{file}_{category}"):
                course_config['uploaded_files'][category].remove(file)
                with open(os.path.join(course_path, 'config.json'), 'w') as json_file:
                    json.dump(course_config, json_file, indent=4)
                st.rerun()
    st.subheader("Upload New Files")
    new_slides = st.file_uploader("Upload Course Slides (PDF, PPT)",
                                  accept_multiple_files=True, key=f"new_slides_{course_code}")
    new_assignments = st.file_uploader(
        "Upload Course Assignments (PDF, DOC)", accept_multiple_files=True, key=f"new_assignments_{course_code}")
    new_syllabus = st.file_uploader(
        "Upload Course Syllabus (PDF)", accept_multiple_files=True, key=f"new_syllabus{course_code}")

    new_files = {
        'slides': new_slides,
        'assignments': new_assignments,
        'syllabus': new_syllabus
    }

    for category, files in new_files.items():
        if files is not None:
            for file in files:
                file_path = os.path.join(course_path, file.name)
                if file.name not in course_config['uploaded_files'].get(category, []):
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    if category not in course_config['uploaded_files']:
                        course_config['uploaded_files'][category] = []
                    course_config['uploaded_files'][category].append(file.name)
                else:
                    st.warning(
                        f"File {file.name} already exists in {category}.")

    if st.button(f"Update Course_{course_code}"):
        with open(os.path.join(course_path, 'config.json'), 'w') as json_file:
            json.dump(course_config, json_file, indent=4)
        st.success("Course updated successfully!")


###
# reference: https://github.com/krisograbek/streamlit_chatbot_base
###
def on_submit(action):
    search_course_code = st.session_state['search_course_code']
    input_course_code = st.session_state['input_course_code']

    if action == 'search':
        search_course_code = st.session_state['search_course_code']
        if search_course_code:
            if not check_course_exists(os.path.join('document', search_course_code)):
                st.error(f"Course {search_course_code} does not exist")
                return
            st.session_state['course_code'] = search_course_code
            st.session_state['page'] = 'chat'
            st.success(f"Course {search_course_code} found!")
        else:
            st.error("Please input course code")
    elif action == 'create':
        course_code = input_course_code
        st.session_state['course_code'] = course_code
        course_description = st.session_state['input_course_description']
        course_system_prompt = st.session_state['input_course_system_prompt']
        save_path = os.path.join('document', course_code)
        os.makedirs(save_path, exist_ok=True)

        file_categories = {
            'slides': st.session_state['input_uploaded_slides'],
            'assignments': st.session_state['input_uploaded_assignments'],
            'syllabus': st.session_state['input_uploaded_syllabus']
        }

        uploaded_files_info = {}

        for category, files in file_categories.items():
            if files is not None:
                category_files = []
                for file in files:
                    file_path = os.path.join(save_path, file.name)
                    category_files.append(file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                uploaded_files_info[category] = category_files

        config_data = {
            'course_code': course_code,
            'course_description': course_description,
            'uploaded_files': uploaded_files_info,
            'system_prompt': course_system_prompt
        }

        with open(os.path.join(save_path, 'config.json'), 'w') as json_file:
            json.dump(config_data, json_file, indent=4)
        st.session_state['page'] = 'chat'


def show_input_form():
    st.title("Welcome to AI Tutor Pipeline!")
    st.title("Create New Tutor Chatbot")

    st.session_state['input_course_code'] = st.text_input("Course Code")
    st.session_state['input_course_description'] = st.text_area(
        "Course Description")
    st.session_state['input_course_system_prompt'] = st.text_area(
        "Instructor Prompt")

    st.session_state['input_uploaded_slides'] = st.file_uploader(
        "Upload Course Slides (PDF, PPT)", accept_multiple_files=True, key="slides")
    st.session_state['input_uploaded_assignments'] = st.file_uploader(
        "Upload Course Assignments (PDF, DOC)", accept_multiple_files=True, key="assignments")
    st.session_state['input_uploaded_syllabus'] = st.file_uploader(
        "Upload Course Syllabus (PDF)", accept_multiple_files=True, key="syllabus")

    create_button = st.button(
        'Create Course', on_click=on_submit, args=('create',))


def show_chat(course_code):
    st.title("AI Tutor Chat for " + course_code)   
    course_path = os.path.join('document', course_code)
    with open(os.path.join(course_path, 'config.json'), 'r') as json_file:
        course_config = json.load(json_file)
        historical_messages = course_config.get("messages", [])

    for message in historical_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    chat_input = st.text_input("Your prompt", key='chat_input')
    submit_chat = st.button('Chat!', on_click=handle_chat_input)

    if st.button("Clear Chat History"):
        delete_chat_history(course_code)
        if f'agent_{course_code}' in st.session_state:
            st.session_state[f'agent_{course_code}'].reset()
        st.session_state.messages = []
        st.rerun()

    if st.button("Update Course"):
        st.session_state['page'] = 'update'
        st.rerun()


def add_message(course_code, role, content):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append({"role": role, "content": content})

    course_path = os.path.join('document', course_code)
    with open(os.path.join(course_path, 'config.json'), 'r+') as json_file:
        course_config = json.load(json_file)
        if "messages" not in course_config:
            course_config["messages"] = []
        course_config["messages"].append({"role": role, "content": content})
        json_file.seek(0)
        json.dump(course_config, json_file, indent=4)
        json_file.truncate()


def delete_chat_history(course_code):
    course_path = os.path.join('document', course_code)
    with open(os.path.join(course_path, 'config.json'), 'r+') as json_file:
        course_config = json.load(json_file)
        course_config["messages"] = []
        json_file.seek(0)
        json.dump(course_config, json_file, indent=4)
        json_file.truncate()


def handle_chat_input():
    user_input = st.session_state.get('chat_input', '')
    if user_input:
        course_code = st.session_state['course_code']
        add_message(course_code, "user", user_input)
        ai_response = get_ai_response(user_input, course_code).response
        add_message(course_code, "assistant", ai_response)
        st.session_state['chat_input'] = ''


def main():
    add_custom_css()
    if 'page' not in st.session_state:
        st.session_state['page'] = 'input'
        st.session_state['course_code'] = ''
        st.session_state.messages = []

    with st.sidebar:
        st.title("Courses")
        st.markdown("## Create New Course")
        if st.button("Click Me!"):
            st.session_state['page'] = 'input'
            st.session_state['course_code'] = ''
            st.session_state['search_course_code'] = ''
            st.session_state['input_course_code'] = ''
            st.session_state['input_course_description'] = ''
            st.session_state['input_course_system_prompt'] = ''
            st.session_state['input_uploaded_files'] = ''
            st.session_state.messages = []
        st.markdown("---")
        st.markdown("## Search Course")
        st.session_state['search_course_code'] = st.text_input(
            "Search Course by Code")
        if st.button('Search Course!'):
            on_submit('search')
        st.markdown("---")
        st.markdown("## Created Courses")
        for course in get_all_courses('document'):
            if st.button(course):
                st.session_state['course_code'] = course
                st.session_state['page'] = 'chat'
    course_code = st.session_state['course_code']
    if course_code:
        if f'agent_{course_code}' not in st.session_state:
            with st.spinner("Loading AI Tutor..."):
                agent = create_course_agent(course_code)
            st.session_state[f'agent_{course_code}'] = agent
    if st.session_state['page'] == 'input':
        show_input_form()
    elif st.session_state['page'] == 'chat':
        show_chat(st.session_state['course_code'])
    elif st.session_state['page'] == 'update':
        show_update_course_form(st.session_state['course_code'])


if __name__ == "__main__":
    main()
