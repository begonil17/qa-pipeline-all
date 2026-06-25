from pathlib import Path


RAW_QA_DIR = Path("data/output/raw_qa")
# NUGGET_DIR = Path("data/output/nuggets")
# NUGGET_QA_DIR = Path("data/output/nugget_qa")

SCRIPT_DIR = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"
NUGGET_DIR = OUTPUT_DIR / "nuggets"
NUGGET_QA_DIR = OUTPUT_DIR / "nugget_qa"


def folder_size_bytes(folder: Path) -> int:
    if not folder.exists():
        return 0

    return sum(
        file.stat().st_size
        for file in folder.rglob("*")
        if file.is_file()
    )


def format_size(size_bytes: int) -> str:
    kb = size_bytes / 1024
    mb = kb / 1024

    if mb >= 1:
        return f"{mb:.3f} MB"
    return f"{kb:.2f} KB"


def main():
    #raw_qa_size = folder_size_bytes(RAW_QA_DIR)

    nugget_only_size = folder_size_bytes(NUGGET_DIR)
    nugget_qa_size = folder_size_bytes(NUGGET_QA_DIR)
    total_nugget_system_size = nugget_only_size + nugget_qa_size

    print("=== Output Storage Size ===")
    #print(f"Raw QA only: {format_size(raw_qa_size)}")
    print()
    print(f"Nuggets only: {format_size(nugget_only_size)}")
    print(f"Nugget-linked QA only: {format_size(nugget_qa_size)}")
    print(f"Total Nugget QA system: {format_size(total_nugget_system_size)}")
    print()

    #if raw_qa_size > 0:
    #   diff = raw_qa_size - total_nugget_system_size
    #   percent = (diff / raw_qa_size) * 100
    #
    #   if diff > 0:
    #        print(f"Nugget approach saves: {format_size(diff)} ({percent:.2f}%)")
    #   else:
    #       print(f"Nugget approach uses more: {format_size(abs(diff))} ({abs(percent):.2f}%)")


if __name__ == "__main__":
    main()