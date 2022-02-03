import json
from typing import Dict

import pytest

from UVAuth import load_course, COURSE_PATH


@pytest.fixture
def courses():
    with open(COURSE_PATH) as f:
        courses: Dict = json.load(f)
    return courses


def test_courses_file_loading(courses):
    x = list(courses.items())[0]
    assert x[1]["instructor"] == load_course(x[0])["instructor"]


def test_invalid_course(courses):
    assert load_course("this_had_better_not_be_#@a_course") is None
