import json

import typst
from django.conf import settings


def render_typst(name: str, context: dict) -> bytes:
    ctx_json = json.dumps(context)

    root_path = settings.BASE_DIR / "poukazky" / "app" / "typst"
    output = typst.compile(
        input=root_path / name,
        root=root_path,
        font_paths=[root_path / "fonts"],
        output=None,
        format="pdf",
        sys_inputs={"context": ctx_json},
    )

    return output
