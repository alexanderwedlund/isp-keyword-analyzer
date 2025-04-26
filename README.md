# ISP Keyword Analyzer

## Overview

ISP Keyword Analyzer is a specialized tool designed to analyze Information Security Policies (ISPs) by extracting and categorizing sentences containing specific keywords. This tool was developed by Alexander Wedlund to support master thesis research conducted by Alexander Wedlund and Solan Shekany at Örebro University (2025). The project was developed using a combination of manual programming and AI assistance, leveraging Claude Sonnet 3.7 and ChatGPT o3-mini-high to enhance development efficiency and code quality, along with Gemini 2.5 Pro Experimental for generating test ISP documents.

## Features

- Upload and process ISP documents in text or PDF format
- Automatic extraction of sentences containing predefined keywords
- Interactive classification of sentences as either:
  - Actionable Advice (AA): Specific, unambiguous instructions
  - Other Information (OI): General, ambiguous, or non-actionable content
- Calculation of "Keyword Loss of Specificity" metrics both for individual keywords and overall
- Built-in support for Swedish and English language ISPs, with the ability to add more languages through configuration
- Session management for saving and resuming analysis
- Excel export of analysis results with detailed metrics
- Context viewing functionality that displays surrounding sentences when analyzing keywords to improve classification accuracy
- AI-assisted classification of sentences for faster analysis

## Project Structure

```
/
├── app.py                  # Main application entry point
├── requirements.txt        # Project dependencies
├── models/                 # Contains AI model files (placeholders and download links)
├── src/                    # Source code
│   ├── config/             # Configuration settings and keyword definitions
│   ├── data/               # Data handling (file reading, sessions, exports)
│   │   ├── file/           # PDF and text file processing
│   │   ├── exporters/      # Excel export functionality
│   │   └── session_store.py # Session management
│   ├── domain/             # Domain logic
│   │   ├── analyzer.py     # Sentence extraction logic
│   │   ├── metrics.py      # Analysis metrics calculation
│   │   └── ai/             # AI classification functionality
│   └── ui/                 # User interface components
│       ├── app.py          # Main UI setup
│       ├── components/     # Reusable UI elements (sidebar, tables)
│       └── pages/          # Page-specific UI (analysis, upload, export)
└── test_data/              # Contains test data and sample ISP documents
```

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

3. For AI-assisted classification, a Gemma model placeholder and download link are provided in the `/models` directory. Follow the instructions there to download the model from Kaggle.

### Enabling CUDA Support on Windows

I used the following commands to activate CUDA support for GPU acceleration with llama-cpp-python-0.3.8:

```cmd
set CMAKE_ARGS=-DGGML_CUDA=on -DGGML_CUDA_FORCE_CUBLAS=on -DLLAVA_BUILD=off -DCMAKE_CUDA_ARCHITECTURES=native
set FORCE_CMAKE=1
pip install llama-cpp-python --no-cache-dir --force-reinstall --upgrade
```

#### What These Commands Do

- `CMAKE_ARGS=-DGGML_CUDA=on`: Enables CUDA support in the underlying GGML library
- `-DGGML_CUDA_FORCE_CUBLAS=on`: Forces the use of NVIDIA's cuBLAS library for better performance
- `-DLLAVA_BUILD=off`: Disables building LLaVA components we don't need
- `-DCMAKE_CUDA_ARCHITECTURES=native`: Optimizes for your specific GPU architecture
- `FORCE_CMAKE=1`: Forces CMake to rebuild the package
- `--no-cache-dir --force-reinstall --upgrade`: Ensures a clean installation

#### Requirements

This GPU acceleration has been tested with:
- Windows 11
- CUDA Toolkit 12.6
- NVIDIA RTX 3080 (16GB)
- Python 3.12

## Usage

### Running the Application

To start the ISP Analyzer application, run the following command in Windows PowerShell:

```
python -m streamlit run app.py
```

For UNIX/Linux/macOS systems, use:

```
python3 -m streamlit run app.py
```

### Analysis Workflow

1. **Add a new ISP**: Upload a document and provide a name for the ISP
2. **Select a keyword**: Choose a specific keyword from the predefined list for analysis, or proceed with the default first keyword that appears in the selection menu
3. **Classify sentences**: For each sentence containing the keyword, determine if it provides:
   - Actionable Advice (AA): Clear, specific guidance
   - Other Information (OI): General information or ambiguous instructions
4. **Use AI-assisted classification**: Use the AI feature to speed up the classification process
   - Select "Analyze Current Keyword with AI" to analyze the current keyword
   - Select "Analyze All Keywords with AI" to analyze all remaining keywords
   - **Note:** AI classification should be viewed as a starting point and results should be carefully reviewed
5. **Use context when needed**: Toggle the Context button to view surrounding sentences for better understanding of how the keyword is used in its larger textual environment
6. **Save your progress**: You can save your session anytime
7. **Export data**: Generate an Excel file with analysis results

## AI-assisted Classification

ISP Keyword Analyzer includes AI-assisted classification that can:
- Analyze individual keywords or all remaining keywords
- Suggest classifications based on sentence context and language
- Significantly speed up the analysis process

### Important notes about the AI functionality:

- **Use with caution**: AI classifications should always be reviewed by a human for accuracy
- **Starting point, not final answer**: Consider AI suggestions as a starting point, not a definitive answer
- **Performance considerations**: AI analysis uses local computation and may be slow on computers without GPU support

When using "Analyze Current Keyword with AI" or "Analyze All Keywords with AI", the tool will warn you about potential errors and ask for confirmation before proceeding.

## Technical Details

The application is built using:
- Streamlit for the web interface
- PyPDF2 for PDF document processing
- SQLite for session state management
- Pandas and XlsxWriter for data manipulation and export
- Llama-cpp-python for local AI inference

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

- **Keyword Loop**: When selecting a keyword that has already been analyzed and clicking "Next Keyword," the user becomes stuck on that keyword. To exit the loop, manually select the next word.
- **AI Classification Accuracy**: AI classifications may sometimes be incorrect, especially for complex sentences or ambiguous contexts. All AI-generated classifications should be reviewed by a human for accuracy.
- **GPU Support Configuration**: GPU support requires proper CUDA and llama-cpp-python configuration, otherwise CPU is used which may be significantly slower, especially for the 12B model.
- **AI Interface Aesthetics**: The AI analysis interface currently displays excessive logs and diagnostic information, creating a cluttered appearance during model loading and inference operations.