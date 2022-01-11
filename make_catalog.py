import os
from argparse import ArgumentParser
import pandas as pd
from tqdm import tqdm
from paper_meta_info import PaperMetaInfo


def main():
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default="catalog.csv")
    parser.add_argument('document_root_dir', type=str, help='document root directory')
    args = parser.parse_args()

    file_list = []
    for curDir, dirs, files in os.walk(args.document_root_dir):
        dirpath = curDir.replace(args.document_root_dir, "").lstrip("/")
        for filename in files:
            if filename.endswith(".pdf"):
                filepath = os.path.join(args.document_root_dir, dirpath, filename)
                file_list.append({'filename': filename, 'dirpath': dirpath, 'filepath': filepath})
    print(f"Found {len(file_list)} papers")

    print("Extracting title and abstract...")
    extractor = PaperMetaInfo()
    for fileinfo in tqdm(file_list):
        print(fileinfo['filepath'])
        title, abstract = extractor.get_title_and_abstract(fileinfo['filepath'])
        fileinfo["title"] = title
        fileinfo["abstract"] = abstract

    df = pd.DataFrame(file_list, columns=["filename", "dirpath", "title", "abstract", "filepath"])
    df.to_csv(args.output, index=False)
    print("Finished.")

if __name__ == "__main__":
    main()
