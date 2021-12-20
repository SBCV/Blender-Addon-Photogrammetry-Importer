import textwrap


def add_multi_line_label(ui_layout, long_text, max_line_length=120):
    text_wrapper = textwrap.TextWrapper(width=max_line_length)
    wrapped_lines = text_wrapper.wrap(text=long_text)
    row = ui_layout.row()
    for text in wrapped_lines:
        row = ui_layout.row()
        row.scale_y = 0.25
        row.label(text=text)
