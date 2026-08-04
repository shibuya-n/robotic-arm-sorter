"""Command-line entry point for the object detection pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.detector import detect_image_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect red, green, and blue objects in an image."
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Path to an input image. You can also pass this with --image.",
    )
    parser.add_argument(
        "--image",
        dest="image_option",
        help="Path to an input image.",
    )
    parser.add_argument(
        "--output",
        help="Path for the annotated image. Defaults to images/output/<name>_annotated.jpg.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path to save the detection JSON.",
    )
    return parser.parse_args()


def default_output_path(input_path: Path) -> Path:
    return Path("images") / "output" / f"{input_path.stem}_annotated.jpg"


def main() -> None:
    args = parse_args()
    image_arg = args.image_option or args.image
    if not image_arg:
        raise SystemExit("Provide an image path, for example: python -m src.main --image images/input/sample.jpg")

    input_path = Path(image_arg)
    annotated_output = Path(args.output) if args.output else default_output_path(input_path)
    result = detect_image_file(
        input_path=input_path,
        annotated_output_path=annotated_output,
        json_output_path=args.json_output,
    )

    print(json.dumps(result, indent=2))
    print(f"Annotated image saved to: {annotated_output}")
    if args.json_output:
        print(f"Detection JSON saved to: {args.json_output}")


if __name__ == "__main__":
    main()
