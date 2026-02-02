import html
from difflib import SequenceMatcher


def generate_side_by_side_diff(left_code, right_code):
    left = left_code.splitlines()
    right = right_code.splitlines()

    sm = SequenceMatcher(None, left, right)

    left_out = []
    right_out = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for l, r in zip(left[i1:i2], right[j1:j2]):
                left_out.append(f"<mark>{html.escape(l)}</mark>")
                right_out.append(f"<mark>{html.escape(r)}</mark>")
        else:
            for l in left[i1:i2]:
                left_out.append(html.escape(l))
            for r in right[j1:j2]:
                right_out.append(html.escape(r))

    return "<br>".join(left_out), "<br>".join(right_out)
