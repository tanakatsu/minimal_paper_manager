import sys
from paper_meta_info import PaperMetaInfo

pdf_file = sys.argv[1]
extractor = PaperMetaInfo(debug=True)
title, abstract = extractor.get_title_and_abstract(pdf_file)
print('Title=', title)
print('Abstract=', abstract)

