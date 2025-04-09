# ISP Keyword Analyzer

## Overview

ISP Analyzer is a specialized tool designed to analyze Information Security Policies (ISPs) by extracting and categorizing sentences containing specific keywords. This tool was developed to support the master thesis research conducted by me and a coursemate at Örebro University

## Features

- Upload and process ISP documents in text or PDF format
- Automatic extraction of sentences containing predefined keywords
- Interactive classification of sentences as either:
  - Actionable Advice (AA): Specific, unambiguous instructions
  - Other Information (OI): General, ambiguous, or non-actionable content
- Calculation of "Keyword Loss of Specificity" metrics both for individual keywords and overall
- Support for both Swedish and English language ISPs
- Session management for saving and resuming analysis
- Excel export of analysis results with detailed metrics

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
python -m streamlit run isp_analyzer.py
```

For UNIX/Linux/macOS systems, use:

```
python3 -m streamlit run isp_analyzer.py
```

### Analysis Workflow

1. **Add a new ISP**: Upload a document and provide a name for the ISP
2. **Select a keyword**: Choose from the predefined list of keywords to analyze
3. **Classify sentences**: For each sentence containing the keyword, determine if it provides:
   - Actionable Advice (AA): Clear, specific guidance
   - Other Information (OI): General information or ambiguous instructions
4. **Review results**: Examine metrics, including the Keyword Loss of Specificity
5. **Export data**: Generate an Excel file with comprehensive analysis results

## Technical Details

The application is built using:
- Streamlit for the web interface
- PyPDF2 for PDF document processing
- SQLite for session state management
- Pandas and XlsxWriter for data manipulation and export

## Methodology

The core analytical framework is based on the "Keyword Loss of Specificity" metric by [Rostami & Karlsson (2024)](https://www.emerald.com/insight/content/doi/10.1108/ics-10-2023-0187/full/pdf), calculated as:

- For individual keywords: `Loss = 100 × (OI occurrences / Total occurrences)`
- For overall assessment: `Total Loss = 100 × (Sum of all OI occurrences / Total keyword occurrences)`

Where:
- AA (Actionable Advice): Number of occurrences where the keyword is used to provide clear, specific, and unambiguous instructions that employees can directly follow
- OI (Other Information): Number of occurrences where the keyword isn't used for actionable advice but instead provides general, vague, or ambiguous information
- Total occurrences: Combined count of both AA and OI instances (AA + OI)
