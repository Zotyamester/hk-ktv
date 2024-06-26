import os
import urllib.request

import PyPDF2

# Source of input files: https://vik.bme.hu/page/62/

paths = [
        'https://vik.bme.hu/document/6098/original/5n_a7_2.pdf',
        'https://vik.bme.hu/document/6100/original/5n_a7_4.pdf',
        'https://vik.bme.hu/document/6099/original/5n_a7_6.pdf',
        'https://vik.bme.hu/document/6101/original/5n_a8_2.pdf',
        'https://vik.bme.hu/document/6102/original/5n_a8_4.pdf',
        'https://vik.bme.hu/document/6108/original/5n_a8_6.pdf',
        'https://vik.bme.hu/document/6103/original/5n_a9_2.pdf',
        'https://vik.bme.hu/document/6104/original/5n_a9_4.pdf',
        'https://vik.bme.hu/document/6118/original/szv_bsc.pdf'
]

# The work around to avoid using BeautifulSoup4 is to insert this
# jQuery statement into the JavaScript console of your browser
# after opening the site above
"""
$('.main-page-container a').each(function(index) { console.log($(this).attr('href'))});
"""

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


def update_days(days, row):
    day_of_week, start_time, end_time, name, neptun_code, course_code, course_type = row

    course_type = abbreviate_course_type(course_type)

    # Presentations are ignored when making the schedule
    if course_type == 'Előadás':
        return

    event = create_event(name, course_type)

    day = days.get(day_of_week, {})
    starting_at = day.get(start_time, set())
    starting_at.add(event)
    day[start_time] = starting_at
    days[day_of_week] = day

def print_days(days, f):
    for day, schedule in sorted(days.items(), key=lambda kv: DAYS_OF_WEEK[kv[0]]):
        print('\t' + day, file=f)
        for start_time, event in sorted(schedule.items(), key=lambda kv: kv[0]):
            print('\t\t' + start_time + ':' +
                    '/'.join(event), file=f)

def make_report(report_filename):
    if not os.path.exists('pdfs'):
        os.mkdir('pdfs')

    with open(report_filename, 'w', encoding='utf-8') as f:
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

                # Prepopulating the days, so that every weekday must appear when printing the dict out
                days = {key: {} for key in DAYS_OF_WEEK}

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

                print(filename, file=f)
                print_days(days, f)


if __name__ == '__main__':
    make_report('report.txt')
