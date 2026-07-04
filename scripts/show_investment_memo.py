from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService


def main():
    service = InvestmentMemoService()
    memo = service.build(InvestmentMemoInput())

    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = out_dir / f"investment_memo_{stamp}.md"
    service.save_markdown(memo["markdown"], md_path)
    csv_paths = service.save_tables(memo["tables"], out_dir / f"investment_memo_{stamp}_tables")

    print("Investment memo created:")
    print(md_path)
    print("\nCSV tables:")
    for path in csv_paths:
        print(path)

    print("\nDecision:")
    print(memo["review"]["decision"])


if __name__ == "__main__":
    main()
