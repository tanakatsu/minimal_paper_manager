import os
from argparse import ArgumentParser
import pandas as pd
from tqdm import tqdm
from paper_meta_info import PaperMetaInfo


COLUMNS = ["filename", "dirpath", "title", "abstract", "filepath"]


def remove_missing_files(df, keep=False):
    missing = df["filepath"].apply(lambda x: not os.path.exists(x))
    df_missing = df[missing]
    if len(df_missing):
        print(f"Found {len(df_missing)} missing files in catalog.")
        for items in df_missing.itertuples():
            print(f"  [missing] {items.filepath}")
        if not keep:
            print("  Removed from catalog")
    if keep:
        return df
    return df[~missing]


def check_newfiles(df_in, df_out):
    df_new = df_out[~df_out["filename"].isin(df_in["filename"].values)]
    if len(df_new):
        print(f"Found {len(df_new)} new files in target directory.")
        for row in df_new.itertuples():
            print(f"  [New] {row.filepath}")


def check_duplication(df):
    srs = df["filename"].value_counts()
    srs = srs[srs >= 2]  # 重複ファイル名を抽出
    if len(srs):
        print(f"Found {len(srs)} duplicated papers.")
        for index, _val in srs.iteritems():
            print(f"  [Duplicated] {index}")
            df_dup = df[df["filename"] == index]
            for row in df_dup.itertuples():
                print(f"    {row.filepath}")


def main():
    parser = ArgumentParser()
    parser.add_argument('-f', '--file', type=str, default="catalog.csv", help='catalog filename')
    parser.add_argument('--keep_missing', action="store_true", help='Keep missing entries from catalog')
    parser.add_argument('--dryrun', action='store_true', help='Just checking. Do not save catalog file')
    parser.add_argument('--update', action='store_true', help='Re-extract title and abstract')
    parser.add_argument('document_root_dir', type=str, help='document root directory')
    args = parser.parse_args()

    catalog_file = args.file
    if os.path.exists(catalog_file):
        df = pd.read_csv(catalog_file)
    else:
        df = pd.DataFrame(columns=COLUMNS)

    # 削除されたレコードの検出
    df = remove_missing_files(df, keep=args.keep_missing)

    file_list = []
    root_dir = os.path.realpath(args.document_root_dir)
    for curDir, dirs, files in os.walk(root_dir):
        dirpath = curDir.replace(root_dir, "").lstrip("/")
        for filename in files:
            if filename.endswith(".pdf"):
                filepath = os.path.join(root_dir, dirpath, filename)
                file_list.append({'filename': filename, 'dirpath': dirpath, 'filepath': filepath})
    print(f"Found {len(file_list)} papers in target directory.")

    print("Extracting title and abstract...")
    extractor = PaperMetaInfo()
    for fileinfo in tqdm(file_list):
        print(fileinfo['filepath'])
        df_matched = df[df['filepath'] == fileinfo['filepath']]
        if len(df_matched) and not args.update:
            # カタログ上のデータを再利用する
            fileinfo["title"] = df_matched.iloc[0]['title']
            fileinfo["abstract"] = df_matched.iloc[0]['abstract']
        else:
            title, abstract = extractor.get_title_and_abstract(fileinfo['filepath'])
            fileinfo["title"] = title
            fileinfo["abstract"] = abstract
            if len(df_matched) and args.update:
                print("Updated")

    df_out = pd.DataFrame(file_list, columns=COLUMNS)

    # 新規追加ファイルのチェック
    check_newfiles(df, df_out)

    # 重複タイトルのチェック
    check_duplication(df_out)

    if args.dryrun:
        print("Finished without saving.")
    else:
        df_out.to_csv(catalog_file, index=False)
        print("Finished.")

if __name__ == "__main__":
    main()
