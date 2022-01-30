import pandas as pd
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("--catalog_file", type=str, default="catalog.csv")
    parser.add_argument("--target", type=str, default=None, choices=["filename", "title", "abstract"])
    parser.add_argument("keyword", type=str, help="search word")
    args = parser.parse_args()

    keyword = args.keyword.lower()
    target = args.target

    df = pd.read_csv(args.catalog_file)

    filenames = df["filename"].values
    titles = df["title"].values
    abstracts = df["abstract"].values

    found_files = []
    for row in df.itertuples():
        if not type(row.title) == str:
            continue

        matched = False
        if (target is None or target == "filename") and keyword in row.filename:
            matched = True
        elif (target is None or target == "title") and (type(row.title) == str and keyword in row.title.lower()):
            matched = True
        elif (target is None or target == "abstract") and (type(row.abstract) == str and keyword in row.abstract.lower()):
            matched = True

        if matched:
            found_files.append(row)

    if found_files:
        print(f"Found {len(found_files)} matched files")
        for row in found_files:
            print(row.filepath, '"' + row.title + '"')
    else:
        print("No matched files")


if __name__ == "__main__":
    main()
