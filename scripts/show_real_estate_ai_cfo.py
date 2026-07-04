from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.real_estate import AcquisitionInput, ExitIRRInput, RealEstateAICFOService


def main():
    service = RealEstateAICFOService()
    review = service.full_review(
        acquisition_input=AcquisitionInput(),
        exit_input=ExitIRRInput(),
    )

    print(review["executive_summary"])
    print("\nPriority Actions:")
    for action in review["priority_actions"]:
        print("-", action)

    print("\nComments:")
    for item in review["comments"]:
        print(f"- {item['title']} | {item['status']} | score={item['score']:.0f}")


if __name__ == "__main__":
    main()
