import html


def generate_side_by_side_diff(left_code, right_code):
    """
    Very simple line‑based highlighter:
    - identical normalized lines are highlighted
    """

    left_lines = left_code.splitlines()
    right_lines = right_code.splitlines()

    # normalize for comparison
    left_norm = [l.strip() for l in left_lines]
    right_norm = [r.strip() for r in right_lines]

    common = set(left_norm) & set(right_norm)

    def highlight(lines, norm_lines):
        out = []
        for raw, norm in zip(lines, norm_lines):
            escaped = html.escape(raw)
            if norm and norm in common:
                out.append(f"<mark>{escaped}</mark>")
            else:
                out.append(escaped)
        return "<br>".join(out)

    left_html = highlight(left_lines, left_norm)
    right_html = highlight(right_lines, right_norm)

    return left_html, right_html
