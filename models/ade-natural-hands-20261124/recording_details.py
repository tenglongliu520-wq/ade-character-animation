"""Extract eye and garment color references from the supplied front frame."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
# The contours include the original upper lash but exclude the surrounding hair.
# Coordinates refer to reference-front.png, 720 x 950.
EYES = {
    "left": [(212,325),(214,313),(222,302),(234,297),(249,299),(259,307),
             (266,319),(268,333),(263,343),(253,350),(241,351),(229,346),(219,338)],
    "right": [(323,334),(325,321),(334,309),(347,303),(361,303),(372,309),
              (379,320),(379,334),(373,344),(364,352),(348,355),(334,351),(326,343)],
}
# Shared base for the face texture and its surrounding exposed skin.
SKIN_RGB = (251, 221, 209)
INNER_EAR_RGB = (246, 187, 178)

EYE_CROPS = {"left": (208,293,272,357), "right": (319,298,383,362)}

if __name__ == "__main__":
    with Image.open(ROOT / "reference-front.png") as frame:
        for name, bounds in EYE_CROPS.items():
            frame.crop(bounds).convert("RGB").resize((256,256), Image.Resampling.LANCZOS).save(
                ROOT / f"eye-{name}.png"
            )
