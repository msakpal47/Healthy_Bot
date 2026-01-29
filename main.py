import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main() -> int:
    parser = argparse.ArgumentParser(prog="healthy", description="RAG app utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    prep = sub.add_parser("prep")
    prep.add_argument("--answers", dest="answers", default=None)
    prep.add_argument("--brand", dest="brand", default=None)
    prep.add_argument("--logo", dest="logo", default=None)
    sub.add_parser("web")
    args = parser.parse_args()
    print(f"Command: {args.cmd}")
    if args.cmd == "ingest":
        from src.ingest import ingest_pdfs
        ingest_pdfs()
        return 0
    if args.cmd == "ask":
        from src.chat import is_index_ready
        print(is_index_ready())
        return 0
    if args.cmd == "prep":
        from src.prep.cli import run
        out = run(answers_path=args.answers, brand=args.brand, logo=args.logo)
        print(out.as_posix())
        return 0
    if args.cmd == "web":
        from src.web.app import run
        run()
        return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
