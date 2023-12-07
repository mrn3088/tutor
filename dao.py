def get_course_config(courses_collection, course_code):
    return courses_collection.find_one({"course_code": course_code})

def update_course_config(courses_collection, course_code, new_config):
    courses_collection.update_one({"course_code": course_code}, {"$set": new_config})