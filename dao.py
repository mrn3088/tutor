def get_course_config(courses_collection, course_code):
    if courses_collection.find_one({"course_code": course_code}) == None:
        # create a new course config
        courses_collection.insert_one({
            "course_code": course_code,
            "course_description": "",
            "uploaded_files": {
                "slides": [],
                "assignments": [],
                "syllabus": []
            },
            "system_prompt": "",
            "course_title": "",
            "messages": []
        })
        return courses_collection.find_one({"course_code": course_code})
    else:
        return courses_collection.find_one({"course_code": course_code})


def update_course_config(courses_collection, course_code, new_config):
    if courses_collection.find_one({"course_code": course_code}) == None:
        # insert to config
        courses_collection.insert_one(new_config)
    else:
        # update config
        courses_collection.update_one(
        {"course_code": course_code}, {"$set": new_config})
