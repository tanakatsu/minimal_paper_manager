import sys
from paper_meta_info import PaperMetaInfo

if not len(sys.argv) == 2:
    print("Usage: python test_onefile.py pdf_file")
    sys.exit(1)

pdf_file = sys.argv[1]
extractor = PaperMetaInfo(debug=True)
title, abstract = extractor.get_title_and_abstract(pdf_file)
print('Title=', title)
print('Abstract=', abstract)

