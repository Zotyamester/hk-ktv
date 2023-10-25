import PyPDF2

# https://vik.bme.hu/page/62/
pdf_file = open('sample.pdf', 'rb')
pdf_reader = PyPDF2.PdfFileReader(pdf_file)

import pandas as pd

table_data = []
for page_num in range(pdf_reader.getNumPages()):
    # Get the page object for the current page number
    page = pdf_reader.getPage(page_num)
    
    # Extract the text from the page
    text = page.extractText()
    
    # Split the text into lines
    lines = text.split('\n')
    
    # Extract the table data from the lines
    for line in lines:
        row = line.split()
        print(row)
        table_data.append(row)