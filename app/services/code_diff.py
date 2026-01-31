import difflib

def generate_side_by_side_diff(code1, code2):
    lines1 = code1.splitlines()
    lines2 = code2.splitlines()

    diff = difflib.ndiff(lines1, lines2)

    left_output = []
    right_output = []

    for line in diff:
        if line.startswith("  "):  # common line
            left_output.append(f"<span class='same'>{line[2:]}</span>")
            right_output.append(f"<span class='same'>{line[2:]}</span>")
        elif line.startswith("- "):  # only in left
            left_output.append(f"<span class='diff'>{line[2:]}</span>")
        elif line.startswith("+ "):  # only in right
            right_output.append(f"<span class='diff'>{line[2:]}</span>")

    return "\n".join(left_output), "\n".join(right_output)
