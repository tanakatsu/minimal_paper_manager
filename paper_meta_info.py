import numpy as np
import re
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams,
    LTContainer,
    LTTextLine,
)

MIN_WIDTH = 30
TITLE_MAX_LINES = 3  # 最大3行分
TITLE_BOTTOM_RATIO = 0.5  # topから50%以内
TITLE_CONNECTING_SPACE = 6.0
INTRODUCTION_MAX_WIDTH = 120

SKIP_CHARACTERS = ['.', '†', '‡', '♭']  # Titleで使わない文字
EXCLUDE_WORDS = ['Energy   and   Buildings', 'sensors']  # 論文誌の名前など除外対象のワード


class PaperMetaInfo(object):
    def __init__(self, min_width=MIN_WIDTH, debug=False):
        self.min_width = min_width
        self.debug = debug

    # https://qiita.com/mima_ita/items/d99afc28b6f51479f850
    def __get_objs(self, layout, results):
        if not isinstance(layout, LTContainer):
            return
        for obj in layout:
            if isinstance(obj, LTTextLine):
                results.append({'bbox': obj.bbox, 'text' : obj.get_text(), 'type' : type(obj)})
            self.__get_objs(obj, results)

    def find_abstract_line(self, parse_results):
        line = -1
        for i, r in enumerate(parse_results):
            txt = r['text'].replace(" ", "").lower()
            if txt.startswith('abstract'):
                line = i
                break
        return line

    def check_character_in_word(self, word, target_characters):
        return any([char for char in word if char in target_characters])

    def find_author_like_word(self, word):
        chk1 = re.search(r'[A-Z]{1}[a-z]+[12][,\s]', word)
        chk2 = re.search(r'[A-Z]{1}[a-z]+,\*{1,2}', word)
        return (chk1 is not None) or (chk2 is not None)

    def get_title_and_abstract(self, filepath):
        with open(filepath, "rb") as f:
            parser = PDFParser(f)
            document = PDFDocument(parser)
            if not document.is_extractable:
                raise PDFTextExtractionNotAllowed
            # https://pdfminersix.readthedocs.io/en/latest/api/composable.html#
            laparams = LAParams(
                all_texts=True,
            )
            rsrcmgr = PDFResourceManager()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(document):
                interpreter.process_page(page)
                layout = device.get_result()
                results = []
                # print('objs-------------------------')
                self.__get_objs(layout, results)

                last_bbox = None
                for r in results:
                    box = r['bbox']  # x0, y0, x1, y1
                    r['height'] = round(box[3] - box[1], 3)  # 小数第3位で丸める
                    r['width'] = round(box[2] - box[0], 3)
                    if r['height'] == 0.0:
                        r['aspect'] = 0.0
                    else:
                        r['aspect'] = r['width'] / r['height']
                    if last_bbox:
                        r['upper_space'] = last_bbox[1] - box[3]
                    else:
                        r['upper_space'] = -1
                    last_bbox = box
                    if self.debug:
                        print(r['height'], r['width'], r['aspect'], r['upper_space'], '"' + r['text'].rstrip() + '"')
                # 1ページ目のみ
                break

        # Title
        title_candidates = [r for r in results if r['width'] > self.min_width]
        abst_line_no = self.find_abstract_line(title_candidates)  # Abstractの行をサーチ
        max_line_no = abst_line_no if abst_line_no >= 0 else int(len(title_candidates) * TITLE_BOTTOM_RATIO)
        title_candidates = [r for i, r in enumerate(title_candidates) if i < max_line_no]

        # 著者情報で含む文字がある場合は除外
        title_candidates = [r for r in title_candidates if not self.check_character_in_word(r['text'], SKIP_CHARACTERS)]

        # 著者情報っぽい行は除外
        title_candidates = [r for r in title_candidates if not self.find_author_like_word(r['text'])]

        # 特定文字列を除外
        title_candidates = [r for r in title_candidates if r['text'].strip() not in EXCLUDE_WORDS]

        max_pos = np.argmax([r['height'] for r in title_candidates])
        max_height = title_candidates[max_pos]['height']
        title_lines = [title_candidates[max_pos]['text'].strip()]
        for pos in range(max_pos+1, min(max_pos+TITLE_MAX_LINES+1, len(title_candidates))):
            if title_candidates[pos]['height'] == max_height:
                title_lines.append(title_candidates[pos]['text'].strip())
        title = ' '.join(title_lines)
        # print(title)

        # 抽出したタイトル行の前後に連結する情報があるかをチェック
        start_line = [i for i, r in enumerate(results) if r['text'].strip() == title_lines[0]][0]
        end_line = [i for i, r in enumerate(results) if r['text'].strip() == title_lines[-1]][0]
        if (title[-1] in ("-", ":")) and (end_line < len(results) - 1):
            # 直後をサーチする
            r = results[end_line+1]
            if r['upper_space'] < TITLE_CONNECTING_SPACE and r['upper_space'] > 0:
                title = title + " " + r['text'].strip()
        elif (title[-1] in ("∗")) and max_pos > 0:  # *ではない
            # 直前をサーチする
            r = results[start_line]
            if r['upper_space'] < TITLE_CONNECTING_SPACE and r['upper_space'] > 0:
                title = title_candidates[max_pos-1]['text'].strip() + " " + title
        elif end_line < len(results) - 1:
            # 直後をサーチする
            r = results[end_line+1]
            if r['upper_space'] < TITLE_CONNECTING_SPACE and r['upper_space'] > 0:
                if not any([char for char in r['text'] if char in [',', '*', '.', '†', '‡', '♭']]):  # Author行っぽくないなら
                    title = title + " " + r['text'].strip()
                    title = title.rstrip()

        # Abstract
        in_abstract = False
        abstract_lines = []
        for r in results:
            if r['text'].replace(" ", "").lower().startswith('abstract'):
                in_abstract = True

            if in_abstract:
                # 1章まで
                if (r['text'].startswith('1') or r['text'].startswith('Introduction') or r['text'].startswith('I. ')) \
                        and (r['width'] < INTRODUCTION_MAX_WIDTH):
                    break
                abstract_lines.append(r['text'].strip())

        abstract = ' '.join(abstract_lines)
        abstract = re.sub('^Abstract', '', abstract)
        abstract = re.sub('^ABSTRACT', '', abstract)
        abstract = re.sub('^A B S T R A C T', '', abstract)
        abstract = re.sub('^a b s t r a c t', '', abstract)
        abstract = abstract.lstrip("\u2014").lstrip(":").lstrip("-").lstrip(".").lstrip()
        # print(abstract)
        return title, abstract


if __name__ == "__main__":
    pdf_file = "sample.pdf"
    extractor = PaperMetaInfo()
    title, abstract = extractor.get_title_and_abstract(pdf_file)
    print('Title=', title)
    print('Abstract=', abstract)

