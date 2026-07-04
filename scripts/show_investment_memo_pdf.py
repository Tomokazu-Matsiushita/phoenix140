from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.investment_memo_pdf_service import InvestmentMemoPDFService
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService


def main():
    memo_service = InvestmentMemoService()
    pdf_service = InvestmentMemoPDFService()

    memo = memo_service.build(InvestmentMemoInput())
    pdf_bytes = pdf_service.build_pdf_bytes(memo)

    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = out_dir / f"investment_memo_{stamp}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    print("PDF investment memo created:")
    print(pdf_path)
    print("bytes:", len(pdf_bytes))
    print("decision:", memo["review"]["decision"])


if __name__ == "__main__":
    main()
