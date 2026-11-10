import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
from datetime import datetime

from checker import run_analysis


# =========================================================
# APPLICATION SETTINGS
# =========================================================

APP_TITLE = "Cadastral Record Checker"

NAVY = "#142D4E"
BLUE = "#245B91"
GREEN = "#238653"
BACKGROUND = "#F2F5F9"
WHITE = "#FFFFFF"
TEXT = "#263648"
GREY = "#68778A"
LIGHT_BLUE = "#EAF2FA"
LIGHT_GREEN = "#EAF5EE"
BORDER = "#DCE3EB"

cadastral_file = ""
survey_file = ""
analysis_results = None


# =========================================================
# SMALL HELPER FUNCTIONS
# =========================================================

def safe_count(value):
    """Return the number of items in a result."""
    try:
        return len(value)
    except TypeError:
        return 0


def clean_heading(column):
    """Make technical column headings easier to understand."""
    heading = str(column).strip()

    replacements = {
        "Calculated Area (Ha)_x": "Cadastral Area (Ha)",
        "Calculated Area (Ha)_y": "Survey Area (Ha)",
        "Calculation Area (Ha)_x": "Cadastral Area (Ha)",
        "Calculation Area (Ha)_y": "Survey Area (Ha)",
        "Calculated Area (Ha)": "Calculated Area (Ha)",
    }

    if heading in replacements:
        return replacements[heading]

    if heading.endswith("_x"):
        heading = heading[:-2] + " (Cadastral)"
    elif heading.endswith("_y"):
        heading = heading[:-2] + " (Survey)"

    return heading.replace("_", " ")


def format_value(value):
    """Format values for display without showing Python objects."""
    if pd.isna(value):
        return "—"

    if isinstance(value, float):
        return f"{value:,.3f}"

    return str(value)


def make_rounded_button(parent, text, command, color, width=200):
    """Create a simple rounded button using a Tkinter Canvas."""
    button = tk.Canvas(
        parent,
        width=width,
        height=44,
        bg=parent.cget("bg"),
        highlightthickness=0,
        cursor="hand2"
    )

    button.create_polygon(
        0, 0,
        width - 12, 0,
        width, 0,
        width, 32,
        width - 12, 44,
        0, 44,
        0, 32,
        0, 0,
        fill=color,
        outline=color,
        smooth=False,
        splinesteps=20
    )

    button.create_text(
        width / 2,
        22,
        text=text,
        fill=WHITE,
        font=("Segoe UI", 9, "bold")
    )

    button.bind("<Button-1>", lambda event: command())
    return button


def show_table(parent, data, empty_message):
    """Display a DataFrame in a clean table."""
    for widget in parent.winfo_children():
        widget.destroy()

    if data is None or data.empty:
        tk.Label(
            parent,
            text=empty_message,
            font=("Segoe UI", 10),
            fg=GREEN,
            bg=WHITE,
            pady=18
        ).pack(fill="x")
        return

    table_frame = tk.Frame(parent, bg=WHITE)
    table_frame.pack(fill="both", expand=True)

    columns = [str(column) for column in data.columns]

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings"
    )

    vertical_scroll = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )

    horizontal_scroll = ttk.Scrollbar(
        table_frame,
        orient="horizontal",
        command=tree.xview
    )

    tree.configure(
        yscrollcommand=vertical_scroll.set,
        xscrollcommand=horizontal_scroll.set
    )

    for column in columns:
        tree.heading(column, text=clean_heading(column))
        tree.column(column, width=150, minwidth=100, anchor="center")

    for _, row in data.iterrows():
        values = [format_value(row[column]) for column in data.columns]
        tree.insert("", "end", values=values)

    tree.grid(row=0, column=0, sticky="nsew")
    vertical_scroll.grid(row=0, column=1, sticky="ns")
    horizontal_scroll.grid(row=1, column=0, sticky="ew")

    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)


def make_metric_card(parent, title, value, background, value_color):
    """Create one summary card."""
    card = tk.Frame(
        parent,
        bg=background,
        padx=15,
        pady=12,
        highlightthickness=1,
        highlightbackground=BORDER
    )

    tk.Label(
        card,
        text=str(value),
        font=("Segoe UI", 22, "bold"),
        fg=value_color,
        bg=background
    ).pack(anchor="w")

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 9),
        fg=TEXT,
        bg=background
    ).pack(anchor="w", pady=(3, 0))

    return card


# =========================================================
# FILE SELECTION
# =========================================================

def select_cadastral():
    global cadastral_file

    file_path = filedialog.askopenfilename(
        title="Select Cadastral Records",
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )

    if file_path:
        cadastral_file = file_path
        cadastral_label.config(
            text=os.path.basename(file_path),
            fg=GREEN
        )
        status_label.config(text="Cadastral records selected")


def select_survey():
    global survey_file

    file_path = filedialog.askopenfilename(
        title="Select Survey Records",
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )

    if file_path:
        survey_file = file_path
        survey_label.config(
            text=os.path.basename(file_path),
            fg=GREEN
        )
        status_label.config(text="Survey records selected")


# =========================================================
# DISPLAY ANALYSIS RESULTS
# =========================================================

def display_results(results):
    """Show the analysis in understandable tables and summaries."""

    missing_in_survey = results[0]
    missing_in_cadastral = results[1]
    cadastral_duplicates = results[2]
    survey_duplicates = results[3]
    area_results = results[4]
    coordinate_results = results[5]

    # Remove the previous results from all tabs.
    for widget in overview_content.winfo_children():
        widget.destroy()

    # Summary cards
    duplicate_count = (
        safe_count(cadastral_duplicates)
        + safe_count(survey_duplicates)
    )

    plots_compared = safe_count(area_results)

    cards_frame = tk.Frame(overview_content, bg=WHITE)
    cards_frame.pack(fill="x", padx=15, pady=15)

    cards = [
        ("Missing in survey", safe_count(missing_in_survey),
         LIGHT_BLUE, BLUE),
        ("Missing in cadastral", safe_count(missing_in_cadastral),
         LIGHT_BLUE, BLUE),
        ("Duplicate coordinate records", duplicate_count,
         LIGHT_GREEN, GREEN),
        ("Plots compared", plots_compared,
         LIGHT_GREEN, GREEN)
    ]

    for index, item in enumerate(cards):
        card = make_metric_card(
            cards_frame,
            item[0],
            item[1],
            item[2],
            item[3]
        )
        card.grid(
            row=0,
            column=index,
            padx=5,
            sticky="nsew"
        )
        cards_frame.columnconfigure(index, weight=1)

    # Overall summary
    summary_text = (
        "Analysis completed. Review the tabs to see the detailed findings."
    )

    if (
        safe_count(missing_in_survey) == 0
        and safe_count(missing_in_cadastral) == 0
        and duplicate_count == 0
    ):
        summary_text = (
            "No missing plot numbers or duplicate coordinate records "
            "were detected. Review the area and coordinate comparison "
            "tables for any measured differences."
        )

    tk.Label(
        overview_content,
        text=summary_text,
        font=("Segoe UI", 10),
        fg=TEXT,
        bg=WHITE,
        wraplength=850,
        justify="left"
    ).pack(anchor="w", padx=20, pady=(5, 15))

    # Missing plot details
    missing_frame = tk.Frame(
        missing_tab,
        bg=WHITE,
        padx=15,
        pady=15
    )
    missing_frame.pack(fill="both", expand=True)

    tk.Label(
        missing_frame,
        text="Plots missing in survey records",
        font=("Segoe UI", 11, "bold"),
        fg=NAVY,
        bg=WHITE
    ).pack(anchor="w", pady=(0, 5))

    missing_survey_data = pd.DataFrame({
        "Plot Number": sorted(
            list(missing_in_survey),
            key=lambda item: str(item)
        )
    })

    missing_survey_frame = tk.Frame(missing_frame, bg=WHITE)
    missing_survey_frame.pack(fill="x", expand=False)

    show_table(
        missing_survey_frame,
        missing_survey_data,
        "No plot numbers are missing in the survey records."
    )

    tk.Label(
        missing_frame,
        text="Plots missing in cadastral records",
        font=("Segoe UI", 11, "bold"),
        fg=NAVY,
        bg=WHITE
    ).pack(anchor="w", pady=(18, 5))

    missing_cadastral_data = pd.DataFrame({
        "Plot Number": sorted(
            list(missing_in_cadastral),
            key=lambda item: str(item)
        )
    })

    missing_cadastral_frame = tk.Frame(missing_frame, bg=WHITE)
    missing_cadastral_frame.pack(fill="both", expand=True)

    show_table(
        missing_cadastral_frame,
        missing_cadastral_data,
        "No plot numbers are missing in the cadastral records."
    )

    # Duplicate coordinate details
    duplicates_frame = tk.Frame(
        duplicates_tab,
        bg=WHITE,
        padx=15,
        pady=15
    )
    duplicates_frame.pack(fill="both", expand=True)

    tk.Label(
        duplicates_frame,
        text="Duplicate coordinates in cadastral records",
        font=("Segoe UI", 11, "bold"),
        fg=NAVY,
        bg=WHITE
    ).pack(anchor="w", pady=(0, 5))

    cadastral_duplicates_frame = tk.Frame(duplicates_frame, bg=WHITE)
    cadastral_duplicates_frame.pack(fill="both", expand=True)

    show_table(
        cadastral_duplicates_frame,
        cadastral_duplicates,
        "No duplicate coordinates found in cadastral records."
    )

    tk.Label(
        duplicates_frame,
        text="Duplicate coordinates in survey records",
        font=("Segoe UI", 11, "bold"),
        fg=NAVY,
        bg=WHITE
    ).pack(anchor="w", pady=(18, 5))

    survey_duplicates_frame = tk.Frame(duplicates_frame, bg=WHITE)
    survey_duplicates_frame.pack(fill="both", expand=True)

    show_table(
        survey_duplicates_frame,
        survey_duplicates,
        "No duplicate coordinates found in survey records."
    )

    # Area comparison
    show_table(
        area_tab,
        area_results,
        "No matching plots were available for area comparison."
    )

    # Coordinate comparison
    show_table(
        coordinate_tab,
        coordinate_results,
        "No coordinate comparison results are available."
    )


# =========================================================
# RUN ANALYSIS
# =========================================================

def analyse_records():
    global analysis_results

    if not cadastral_file or not survey_file:
        messagebox.showwarning(
            "Files Required",
            "Please select both the cadastral and survey files."
        )
        return

    try:
        status_label.config(text="Analysing records...")
        root.update_idletasks()

        cadastral_data = pd.read_excel(cadastral_file)
        survey_data = pd.read_excel(survey_file)

        # Check that the coordinate columns are present.
        required_columns = ["Easting", "Northing"]

        for column in required_columns:
            if column not in cadastral_data.columns:
                raise ValueError(
                    f"The cadastral file is missing the '{column}' column."
                )

            if column not in survey_data.columns:
                raise ValueError(
                    f"The survey file is missing the '{column}' column."
                )

        # Convert coordinates to numbers while allowing decimal values.
        for column in required_columns:
            cadastral_data[column] = pd.to_numeric(
                cadastral_data[column],
                errors="raise"
            )

            survey_data[column] = pd.to_numeric(
                survey_data[column],
                errors="raise"
            )

        # Run the existing checking functions.
        results = run_analysis(cadastral_data, survey_data)

        if len(results) < 6:
            raise ValueError(
                "The analysis function did not return all six expected results."
            )

        analysis_results = results

        display_results(results)

        # Open the overview tab after analysis.
        results_tabs.select(overview_tab)

        status_label.config(text="Analysis completed successfully")

    except Exception as error:
        status_label.config(text="Analysis could not be completed")

        messagebox.showerror(
            "Analysis Error",
            str(error)
        )


# =========================================================
# PDF REPORT EXPORT
# =========================================================

def export_report():
    if analysis_results is None:
        messagebox.showwarning(
            "No Analysis Results",
            "Please run the analysis before exporting a report."
        )
        return

    file_path = filedialog.asksaveasfilename(
        title="Save Cadastral Analysis Report",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile="Cadastral_Analysis_Report.pdf"
    )

    if not file_path:
        return

    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import (
            getSampleStyleSheet,
            ParagraphStyle
        )
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            LongTable
        )
        from xml.sax.saxutils import escape

        document = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=colors.HexColor(NAVY),
            alignment=TA_CENTER,
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(GREY),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(BLUE),
            spaceBefore=12,
            spaceAfter=7
        )

        normal_style = ParagraphStyle(
            "ReportNormal",
            parent=styles["Normal"],
            fontSize=8,
            leading=11
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=normal_style,
            fontName="Helvetica-Bold",
            textColor=colors.white
        )

        story = []

        story.append(
            Paragraph("CADASTRAL RECORD CHECKER", title_style)
        )

        story.append(
            Paragraph(
                "DETECTION OF INCONSISTENCIES IN CADASTRAL LAND RECORDS",
                subtitle_style
            )
        )

        story.append(
            Paragraph(
                "CADASTRAL ANALYSIS REPORT",
                heading_style
            )
        )

        story.append(
            Paragraph(
                "Date generated: " + datetime.now().strftime("%d %B %Y, %H:%M"),
                normal_style
            )
        )

        story.append(Spacer(1, 8))

        def add_dataframe_table(data, empty_message):
            """Add a DataFrame to the PDF as a formatted table."""

            if data is None or data.empty:
                story.append(
                    Paragraph(escape(empty_message), normal_style)
                )
                story.append(Spacer(1, 7))
                return

            headings = [
                Paragraph(
                    "<b>" + escape(clean_heading(column)) + "</b>",
                    table_header_style
                )
                for column in data.columns
            ]

            table_data = [headings]

            for _, row in data.iterrows():
                table_row = [
                    Paragraph(
                        escape(format_value(value)),
                        normal_style
                    )
                    for value in row.tolist()
                ]
                table_data.append(table_row)

            table = LongTable(
                table_data,
                repeatRows=1,
                hAlign="LEFT"
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                 colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4,
                 colors.HexColor(BORDER)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F2F5F9")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
            ]))

            story.append(table)
            story.append(Spacer(1, 9))

        missing_survey = pd.DataFrame({
            "Plot Number": sorted(
                list(analysis_results[0]),
                key=lambda item: str(item)
            )
        })

        missing_cadastral = pd.DataFrame({
            "Plot Number": sorted(
                list(analysis_results[1]),
                key=lambda item: str(item)
            )
        })

        story.append(
            Paragraph("1. PLOT NUMBER VERIFICATION", heading_style)
        )

        story.append(
            Paragraph("Plots missing in survey records", normal_style)
        )
        add_dataframe_table(
            missing_survey,
            "No plot numbers are missing in the survey records."
        )

        story.append(
            Paragraph("Plots missing in cadastral records", normal_style)
        )
        add_dataframe_table(
            missing_cadastral,
            "No plot numbers are missing in the cadastral records."
        )

        story.append(
            Paragraph("2. DUPLICATE COORDINATE CHECK", heading_style)
        )

        story.append(
            Paragraph("Cadastral record duplicates", normal_style)
        )
        add_dataframe_table(
            analysis_results[2],
            "No duplicate coordinates found in cadastral records."
        )

        story.append(
            Paragraph("Survey record duplicates", normal_style)
        )
        add_dataframe_table(
            analysis_results[3],
            "No duplicate coordinates found in survey records."
        )

        story.append(
            Paragraph("3. PLOT AREA COMPARISON", heading_style)
        )
        add_dataframe_table(
            analysis_results[4],
            "No matching plots were available for area comparison."
        )

        story.append(
            Paragraph("4. BOUNDARY COORDINATE COMPARISON", heading_style)
        )
        add_dataframe_table(
            analysis_results[5],
            "No coordinate comparison results are available."
        )

        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor(GREY))
            canvas.drawString(
                15 * mm,
                9 * mm,
                "Cadastral Record Checker"
            )
            canvas.drawRightString(
                landscape(A4)[0] - 15 * mm,
                9 * mm,
                "Page " + str(doc.page)
            )
            canvas.restoreState()

        document.build(
            story,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number
        )

        status_label.config(text="PDF report exported successfully")

        messagebox.showinfo(
            "Export Successful",
            "The PDF analysis report has been saved successfully."
        )

    except ImportError:
        messagebox.showerror(
            "PDF Library Missing",
            "ReportLab is required to export PDF reports.\n\n"
            "Install it in the VS Code terminal using:\n"
            "pip install reportlab"
        )

    except Exception as error:
        messagebox.showerror(
            "PDF Export Error",
            str(error)
        )


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()
root.title(APP_TITLE)
root.configure(bg=BACKGROUND)
root.minsize(900, 650)

try:
    root.state("zoomed")
except tk.TclError:
    root.geometry("1200x800")


# =========================================================
# STYLE SETTINGS
# =========================================================

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    font=("Segoe UI", 9),
    rowheight=30,
    background=WHITE,
    foreground=TEXT,
    fieldbackground=WHITE,
    borderwidth=0
)

style.configure(
    "Treeview.Heading",
    font=("Segoe UI", 9, "bold"),
    background=NAVY,
    foreground=WHITE,
    padding=9,
    relief="flat"
)

style.map(
    "Treeview",
    background=[("selected", "#DCEAF7")],
    foreground=[("selected", NAVY)]
)

style.configure(
    "TNotebook",
    background=BACKGROUND,
    borderwidth=0
)

style.configure(
    "TNotebook.Tab",
    font=("Segoe UI", 9, "bold"),
    padding=(15, 9),
    background="#E1E8F0",
    foreground=NAVY
)

style.map(
    "TNotebook.Tab",
    background=[("selected", WHITE)],
    foreground=[("selected", BLUE)]
)


# =========================================================
# HEADER
# =========================================================

header = tk.Frame(
    root,
    bg=NAVY,
    height=105
)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="CADASTRAL RECORD CHECKER",
    font=("Segoe UI", 23, "bold"),
    fg=WHITE,
    bg=NAVY
).pack(pady=(19, 4))

tk.Label(
    header,
    text="DETECTION OF INCONSISTENCIES IN CADASTRAL LAND RECORDS",
    font=("Segoe UI", 9),
    fg="#C5D5E8",
    bg=NAVY
).pack()


# =========================================================
# CENTERED MAIN CONTENT
# =========================================================

content_area = tk.Frame(root, bg=BACKGROUND)
content_area.pack(fill="both", expand=True)

main_frame = tk.Frame(
    content_area,
    bg=BACKGROUND,
    width=1120
)
main_frame.pack(expand=True, padx=20, pady=15)
main_frame.pack_propagate(True)


# =========================================================
# DATASET SELECTION PANEL
# =========================================================

file_frame = tk.Frame(
    main_frame,
    bg=WHITE,
    padx=20,
    pady=15,
    highlightthickness=1,
    highlightbackground=BORDER
)
file_frame.pack(fill="x", pady=(0, 12))

tk.Label(
    file_frame,
    text="DATASET SELECTION",
    font=("Segoe UI", 12, "bold"),
    fg=NAVY,
    bg=WHITE
).pack(anchor="w", pady=(0, 12))


cadastral_row = tk.Frame(file_frame, bg=WHITE)
cadastral_row.pack(fill="x", pady=5)

make_rounded_button(
    cadastral_row,
    "SELECT CADASTRAL FILE",
    select_cadastral,
    BLUE,
    210
).pack(side="left")

cadastral_label = tk.Label(
    cadastral_row,
    text="No file selected",
    font=("Segoe UI", 9),
    fg=GREY,
    bg=WHITE
)
cadastral_label.pack(side="left", padx=15)


survey_row = tk.Frame(file_frame, bg=WHITE)
survey_row.pack(fill="x", pady=5)

make_rounded_button(
    survey_row,
    "SELECT SURVEY FILE",
    select_survey,
    BLUE,
    210
).pack(side="left")

survey_label = tk.Label(
    survey_row,
    text="No file selected",
    font=("Segoe UI", 9),
    fg=GREY,
    bg=WHITE
)
survey_label.pack(side="left", padx=15)


# =========================================================
# ACTION BUTTONS
# =========================================================

button_frame = tk.Frame(main_frame, bg=BACKGROUND)
button_frame.pack(fill="x", pady=(3, 12))

make_rounded_button(
    button_frame,
    "RUN ANALYSIS",
    analyse_records,
    GREEN,
    190
).pack(side="left", padx=(0, 10))

make_rounded_button(
    button_frame,
    "EXPORT PDF REPORT",
    export_report,
    BLUE,
    220
).pack(side="left")


# =========================================================
# RESULTS PANEL AND TABS
# =========================================================

result_frame = tk.Frame(
    main_frame,
    bg=WHITE,
    padx=15,
    pady=12,
    highlightthickness=1,
    highlightbackground=BORDER
)
result_frame.pack(fill="both", expand=True)

tk.Label(
    result_frame,
    text="ANALYSIS RESULTS",
    font=("Segoe UI", 13, "bold"),
    fg=NAVY,
    bg=WHITE
).pack(anchor="w", pady=(0, 10))

results_tabs = ttk.Notebook(result_frame)
results_tabs.pack(fill="both", expand=True)

overview_tab = tk.Frame(results_tabs, bg=WHITE)
missing_tab = tk.Frame(results_tabs, bg=WHITE)
duplicates_tab = tk.Frame(results_tabs, bg=WHITE)
area_tab = tk.Frame(results_tabs, bg=WHITE)
coordinate_tab = tk.Frame(results_tabs, bg=WHITE)

results_tabs.add(overview_tab, text="Overview")
results_tabs.add(missing_tab, text="Missing Plots")
results_tabs.add(duplicates_tab, text="Duplicate Coordinates")
results_tabs.add(area_tab, text="Area Comparison")
results_tabs.add(coordinate_tab, text="Coordinate Comparison")

overview_content = tk.Frame(overview_tab, bg=WHITE)
overview_content.pack(fill="both", expand=True)

tk.Label(
    overview_content,
    text="Welcome to Cadastral Record Checker",
    font=("Segoe UI", 15, "bold"),
    fg=NAVY,
    bg=WHITE
).pack(anchor="w", padx=20, pady=(25, 8))

tk.Label(
    overview_content,
    text=(
        "Select the cadastral records and survey records, then run the "
        "analysis. The system will check plot numbers, duplicate "
        "coordinates, area differences and boundary coordinate "
        "displacement."
    ),
    font=("Segoe UI", 10),
    fg=TEXT,
    bg=WHITE,
    wraplength=850,
    justify="left"
).pack(anchor="w", padx=20, pady=5)


# =========================================================
# STATUS BAR AND FOOTER
# =========================================================

status_label = tk.Label(
    root,
    text="Ready | Waiting for datasets",
    font=("Segoe UI", 9),
    fg=NAVY,
    bg="#E1E8F0",
    anchor="w",
    padx=15,
    pady=7
)
status_label.pack(fill="x")

footer = tk.Label(
    root,
    text="CADASTRAL RECORD CHECKER  |  LAND SURVEYING & GEOMATICS",
    font=("Segoe UI", 8),
    fg=WHITE,
    bg=NAVY,
    pady=8
)
footer.pack(fill="x")


# =========================================================
# START APPLICATION
# =========================================================

root.mainloop()
