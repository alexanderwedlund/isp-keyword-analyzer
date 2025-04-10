# ISP Keyword Analyzer

## Overview

ISP Keyword Analyzer is a specialized tool designed to analyze Information Security Policies (ISPs) by extracting and categorizing sentences containing specific keywords. This tool was developed to support master thesis research conducted by Alexander and Solan at Örebro University.

## Features

- Upload and process ISP documents in text or PDF format
- Automatic extraction of sentences containing predefined keywords
- Interactive classification of sentences as either:
  - Actionable Advice (AA): Specific, unambiguous instructions
  - Other Information (OI): General, ambiguous, or non-actionable content
- Calculation of "Keyword Loss of Specificity" metrics both for individual keywords and overall
- Support for Swedish and English language ISPs
- Session management for saving and resuming analysis
- Excel export of analysis results with detailed metrics
- Context viewing functionality that displays surrounding sentences when analyzing keywords to improve classification accuracy

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Steps

1. Clone this repository:
   ```
   git clone https://github.com/alexanderwedlund/isp-keyword-analyzer.git
   cd isp-keyword-analyzer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

To start the ISP Analyzer application, run the following command in Windows PowerShell:

```
python -m streamlit run isp_keyword_analyzer.py
```

For UNIX/Linux/macOS systems, use:

```
python3 -m streamlit run isp_keyword_analyzer.py
```

### Analysis Workflow

1. **Add a new ISP**: Upload a document and provide a name for the ISP
2. **Select a keyword**: Choose a specific keyword from the predefined list for analysis, or proceed with the default first keyword that appears in the selection menu
3. **Classify sentences**: For each sentence containing the keyword, determine if it provides:
   - Actionable Advice (AA): Clear, specific guidance
   - Other Information (OI): General information or ambiguous instructions
4. **Use context when needed**: Toggle the Context button to view surrounding sentences (previous and next) for better understanding of how the keyword is used in its larger textual environment
5. **Save your progress**: You can save your session anytime
6. **Export data**: Generate an Excel file with analysis results

## Technical Details

The application is built using:
- Streamlit for the web interface
- PyPDF2 for PDF document processing
- SQLite for session state management
- Pandas and XlsxWriter for data manipulation and export

## Methodology

The core analytical framework is based on the "Keyword Loss of Specificity" metric by [Rostami & Karlsson (2024)](https://www.emerald.com/insight/content/doi/10.1108/ics-10-2023-0187/full/pdf), which quantifies how often keywords appear in contexts that don't provide actionable guidance:

- For individual keywords: `Keyword Loss of Specificity = 100 × (OI occurrences / Total occurrences)`
- For overall assessment: `Total Keyword Loss of Specificity = 100 × (Sum of all OI occurrences / Sum of all keyword occurrences)`

Where:
- **AA (Actionable Advice)**: Instances where keywords are used within clear, specific, and unambiguous instructions that employees can directly implement without additional interpretation
- **OI (Other Information)**: Instances where keywords appear in general statements, vague guidance, or non-instructional contexts that don't provide directly implementable actions
- **Total occurrences**: The sum of both AA and OI instances for each keyword (AA + OI)

A lower loss of specificity percentage indicates that keywords are more frequently used to provide clear, actionable guidance rather than general information.

## Known Issues

### Version 2.0
- **Keyword Loop**: When selecting a keyword that has already been analyzed and clicking "Next Keyword," the user becomes stuck on that keyword. To exit the loop, manually select the next word.
