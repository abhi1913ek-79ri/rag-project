from services.pdf_reader import (
    open_pdf,
    extract_page_text,
    extract_all_pages,
    split_into_paragraphs
)

pdf = open_pdf("documents/sample.pdf")


""""""
# # 1
# print("Pdf Successfuly Opened")
# print("Pages :",len(pdf))

# 2
text = extract_page_text(pdf, 0)
print("\n--- PAGE 1 TEXT ---")
print(text)

# # 3
# pages = extract_all_pages(pdf)

# print("\nTotal extracted pages:", len(pages))

# for page in pages:
#     print("Page:", page["page"])
#     print("Text length:", len(page["text"]))

# ---------------------------------------
paragraphs = split_into_paragraphs(text)

print("\nTotal paragraphs on Page 1:", len(paragraphs))

for i, paragraph in enumerate(paragraphs, start=1):
    print(f"\n--- Paragraph {i} ---")
    print(paragraph)


# print("\n--- RAW TEXT STRUCTURE ---")
# print(repr(text))