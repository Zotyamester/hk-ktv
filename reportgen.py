import os
import urllib.request
import pandas as pd

import PyPDF2

# Source of input files: https://vik.bme.hu/page/62/
# DEPRECATED: It is no longer needed to download the files from the website, you can just ask directly for the XLSX file.
_paths = []

# The work around to avoid using BeautifulSoup4 is to insert this
# jQuery statement into the JavaScript console of your browser
# after opening the site above
"""
$('.main-page-container a').each(function(index) { console.log($(this).attr('href'))});
"""


PROGRAM_CODE = {
    "7": "vill",
    "8": "inf",
    "9": "bprof",
}


# Only including workdays
DAYS_OF_WEEK = {"Hétfő": 1, "Kedd": 2, "Szerda": 3, "Csütörtök": 4, "Péntek": 5}


# Abbreviates the given course type, if applicable,
# otherwise returns an empty string as an abbreviation
def abbreviate_course_type(course_type: str) -> str:
    mapping = {
        "Gyakorlat": "Gyak",
        "Labor": "Lab",
        "Elmélet": "Előadás",
        "Zárthelyi": "ZH",
    }

    return mapping.get(course_type, "")


# Forms a string representing an event from a name and a course abbreviation
def create_event(name, course_abbr):
    if course_abbr == "":
        return name
    return "%s %s" % (name, course_abbr)


def update_days(days: pd.DataFrame, row):
    day, start_time, end_time, name, course_type = row

    end_time_tokens = end_time.split(":")
    end_time_as_minutes = int(end_time_tokens[0]) * 60 + int(end_time_tokens[1])

    start_time_tokens = start_time.split(":")
    start_time_as_minutes = int(start_time_tokens[0]) * 60 + int(start_time_tokens[1])

    duration = (end_time_as_minutes - start_time_as_minutes + 59) // 60

    # Presentations are ignored when making the schedule
    if name == "Zárthelyi":
        course_type = "Zárthelyi"
    elif course_type != "Elmélet":
        course_type = abbreviate_course_type(course_type)
    else:
        return

    event = create_event(name, course_type)
    for _ in range(duration):
        start_time = "%02d:%02d" % (start_time_as_minutes // 60, 00)
        days.at[start_time, day] += (
            " / " if days.at[start_time, day] != "" else ""
        ) + event
        start_time_as_minutes += 60


def make_report(report_name):
    days_per_group = {}

    with pd.ExcelWriter(f"{report_name}.xlsx") as writer:

        # Read sheets from the Excel file
        dfs = pd.read_excel("orarend.xlsx", sheet_name=None)
        # Flatten the dictionary of DataFrames into a single list of DataFrames
        df = pd.concat(dfs.values(), ignore_index=True)

        for ((group, *row), *_) in df.groupby(
            ["Órarend", "A hét napja", "Tól", "Ig", "Tárgynév", "Kurzus típusa"]
        ):
            # Ignore eletives, PhD and MSc courses
            if "SZVT" in group or "Doktori" in group or group[3] == "M":
                continue

            program = PROGRAM_CODE[group[4]]
            semester = group[6]
            group = (program, semester)

            if group not in days_per_group:
                # Make a pandas DataFrame with DAYS_OF_WEEK x hours (from 8 to 20)
                days_per_group[group] = pd.DataFrame(
                    {
                        day: {("%02d:%02d" % (hour, 0)): "" for hour in range(8, 20)}
                        for day in DAYS_OF_WEEK.keys()
                    }
                )
            days = days_per_group[group]
            update_days(days, row)

        # Print DataFrame to Excel sheet
        for (program, semester), days in days_per_group.items():
            days.to_excel(writer, sheet_name=f"{program} {semester}")


if __name__ == "__main__":
    make_report("schedule")
