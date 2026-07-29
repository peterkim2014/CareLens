from app.db.seeds.evidence import (
    seed_evidence_documents,
)
from app.db.session import SessionFactory


def main() -> None:
    with SessionFactory() as session:
        result = seed_evidence_documents(
            session,
        )

    print("Evidence seed completed.")
    print(f"Inserted: {result.inserted}")
    print(f"Updated: {result.updated}")
    print(f"Unchanged: {result.unchanged}")
    print(f"Total processed: {result.total}")


if __name__ == "__main__":
    main()
