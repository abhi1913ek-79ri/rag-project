import pymupdf


def open_pdf(file_path):
    document = pymupdf.open(file_path)
    return document

def extract_page_text(document,page_number):
    page = document[page_number]
    text = page.get_text()
    return text

def extract_all_pages(document):
    pages = []

    for page_number in range(len(document)):
        page = document[page_number]
        text = page.get_text()

        pages.append({
            "page":page_number+1,
            "text":text
        })

    return pages


def split_into_paragraphs(text):
    paragraphs = text.split("\n \n")

    cleaned_paragraphs = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if paragraph:
            cleaned_paragraphs.append(paragraph)

    return cleaned_paragraphs
