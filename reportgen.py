import os
import urllib.request
import pandas as pd

import PyPDF2

# Source of input files: https://vik.bme.hu/page/62/

paths = [
    'https://vik.bme.hu/document/6390/original/5na71.pdf',
    'https://vik.bme.hu/document/6391/original/5na73.pdf',
    'https://vik.bme.hu/document/6395/original/5na75.pdf',
    'https://vik.bme.hu/document/6392/original/5na81.pdf',
    'https://vik.bme.hu/document/6393/original/5na83.pdf',
    'https://vik.bme.hu/document/6394/original/5na85.pdf',
    'https://vik.bme.hu/document/6399/original/5na87.pdf',
    'https://vik.bme.hu/document/6396/original/5na91.pdf',
    'https://vik.bme.hu/document/6397/original/5na93.pdf',
    'https://vik.bme.hu/document/6398/original/5na95.pdf',
    # 'https://vik.bme.hu/document/6413/original/szvtx.pdf',
]

# The work around to avoid using BeautifulSoup4 is to insert this
# jQuery statement into the JavaScript console of your browser
# after opening the site above
"""
$('.main-page-container a').each(function(index) { console.log($(this).attr('href'))});
"""

COURSE_CODE = {
    "7": "vill",
    "8": "inf",
    "9": "bprof",
}

# Only including workdays
DAYS_OF_WEEK = {'Hétfő': 1, 'Kedd': 2,
                'Szerda': 3, 'Csütörtök': 4, 'Péntek': 5}


# Abbreviates the given course type, if applicable,
# otherwise returns an empty string as an abbreviation

def abbreviate_course_type(course_type: str) -> str:
    mapping = {
        'Gyakorlat': 'Gyak',
        'Labor': 'Lab',
        'Elmélet': 'Előadás',
        'Zárthelyi': 'ZH'
    }

    return mapping.get(course_type, '')

# Forms a string representing an event from a name and a course abbreviation


def create_event(name, course_abbr):
    if course_abbr == '':
        return name
    return '%s %s' % (name, course_abbr)

# Parses a line into a set of columns so that together they form a row


def process_line(line):
    row = line.split()
    if row[0] not in DAYS_OF_WEEK:  # Skip if not even the date is given
        return []

    neptun_code_idx = 0
    while neptun_code_idx < len(row) and not row[neptun_code_idx].startswith('BME'):
        neptun_code_idx += 1
    return row[:3] + [' '.join(row[3:neptun_code_idx])] + row[neptun_code_idx:neptun_code_idx + 3]


def update_days(days: pd.DataFrame, row):
    day_of_week, start_time, end_time, name, neptun_code, course_code, course_type = row

    end_time_tokens = end_time.split(':')
    end_time_as_minutes = int(end_time_tokens[0]) * 60 + int(end_time_tokens[1])

    start_time_tokens = start_time.split(':')
    start_time_as_minutes = int(start_time_tokens[0]) * 60 + int(start_time_tokens[1])

    duration = (end_time_as_minutes - start_time_as_minutes + 59) // 60

    course_type = abbreviate_course_type(course_type)

    # Presentations are ignored when making the schedule
    if course_type == 'Előadás':
        return

    event = create_event(name, course_type)
    for i in range(duration):
        start_time = '%02d:%02d' % (start_time_as_minutes // 60, 00)
        days[day_of_week][start_time].append(event)
        start_time_as_minutes += 60

def make_report(report_name):
    if not os.path.exists('pdfs'):
        os.mkdir('pdfs')

    with pd.ExcelWriter(f"{report_name}.xlsx") as writer:
        for path in paths:
            filename = os.path.basename(path)
            input_filename = os.path.join('pdfs', filename)
            if not os.path.exists(input_filename):
                urllib.request.urlretrieve(path, input_filename)

            with open(input_filename, 'rb') as pdf_file:
                pdf_reader = None
                try:
                    pdf_reader = PyPDF2.PdfFileReader(pdf_file, strict=False)
                except:
                    print('SKIPPED %s' % filename)
                    continue

                # Make a pandas DataFrame with DAYS_OF_WEEK x hours (from 8 to 20)
                days = pd.DataFrame({day: {('%02d:%02d' % (hour, 0)): [] for hour in range(8, 20)} for day in DAYS_OF_WEEK.keys()})

                for page_num in range(pdf_reader.getNumPages()):
                    # Get the page object for the current page number
                    page = pdf_reader.getPage(page_num)

                    # Extract the text from the page
                    text = page.extractText()

                    # Split the text into lines
                    lines = text.split('\n')

                    # Extract the table data from the lines
                    for line in lines:
                        row = process_line(line)
                        if len(row) >= 7:
                            update_days(days, row)
                        else:
                            print('SKIPPED: %s' % line)

                # Flatten the third dimension of the DataFrame by concatenating the strings (separated by a '/')
                for day in days.columns:
                    for hour in days.index:
                        days[day][hour] = ' / '.join(set(days[day][hour]))

                # Print DataFrame to Excel sheet
                filename_without_extension = '.'.join(filename.split('.')[:-1])
                course = COURSE_CODE[filename_without_extension[3]]
                semester = filename_without_extension[4]
                days.to_excel(writer, sheet_name=f"{course} {semester}")


if __name__ == '__main__':
    make_report('report')
