# Resume-Importer

## Overview
Resume Importer is a Python tool that extracts structured information from resumes in various formats and converts them to a standardized JSON format. The tool supports multiple input formats and uses a combination of regex patterns and optional transformer-based AI models to extract information accurately.

## Features
- Extract information from multiple resume formats:
PDF resumes
Word/DOCX documents
LinkedIn data exports
- Extract key resume sections:
Personal information
Contact details
Work experience
Education
Skills
Projects
Certifications
Languages
- Optional AI-powered extraction using transformer models
- Configurable debug mode
- Standardized JSON output format
## Installation
### Requirements
Python 3.6+
pip (Python package manager)
### Basic Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/Resume-Importer.git
cd Resume-Importer

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install basic dependencies
pip install pdfminer.six python-docx PyPDF2
```
### Optional Dependencies
```bash
# For OCR capabilities (recommended for scanned PDFs)
pip install pdf2image pytesseract
# Note: You also need to install Tesseract OCR on your system:
# Ubuntu: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract

# For AI-powered extraction
pip install transformers torch
```
## Usage
### Basic Usage
```bash
python resume_importer.py --input <path_to_resume> --output <output_json_file> --format <format_type>
```
### Examples
```bash
# Process a PDF resume
python resume_importer.py --input resumes/example.pdf --output resume_data.json --format pdf

# Process a Word document
python resume_importer.py --input resumes/example.docx --output resume_data.json --format docx

# Process a LinkedIn data export directory
python resume_importer.py --input linkedin_export_dir --output resume_data.json --format linkedin

# Enable debug mode for detailed output
python resume_importer.py --input resumes/example.pdf --output resume_data.json --format pdf --debug

# Use transformer models for enhanced extraction
python resume_importer.py --input resumes/example.pdf --output resume_data.json --format pdf --use-transformers
```
## Supported Input Formats
### PDF Resumes
The tool supports text-based PDFs and can also process scanned PDFs when OCR dependencies are installed.
### Word Documents
Microsoft Word (.docx) files are supported.
### LinkedIn Data Exports
Directories containing CSV files from LinkedIn data exports. [Learn how to download your LinkedIn data](https://www.linkedin.com/help/linkedin/answer/a1339364).
## Output Format
The tool produces a JSON file following the [JSON Resume schema](https://jsonresume.org/schema) with the following structure:
```json
{
  "metadata": {
    "generated_at": "2025-04-03T10:15:30",
    "confidence_score": 85.5,
    "fields_extracted": 24
  },
  "resume_data": {
    "basics": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "555-123-4567",
      "profiles": [
        {
          "network": "LinkedIn",
          "url": "https://linkedin.com/in/johndoe"
        }
      ]
    },
    "work": [
      {
        "name": "Example Company",
        "position": "Software Engineer",
        "startDate": "2020",
        "endDate": "Present"
      }
    ],
    "education": [
      {
        "institution": "University of Example",
        "area": "Computer Science",
        "studyType": "Bachelor's Degree"
      }
    ]
  }
}
```
## Advanced Usage
For more accurate extraction, especially with unstructured or complex resumes:
```bash
python resume_importer.py --input resume.pdf --output data.json --format pdf --use-transformers
```
Note: The first run with transformers will download the required models.
## Troubleshooting
### OCR Issues
- If text extraction from PDFs is poor, ensure Tesseract OCR is properly installed.
- Try increasing the resolution: convert -density 300 input.pdf output.pdf
### Missing Dependencies
- Run pip install -r requirements.txt to ensure all required packages are installed.
## Contributing
Contributions are welcome! Here's how you can contribute:
1. Fork the repository
2. Create your feature branch `git checkout -b feature/[feature_name]`
3. Commit your changes `git commit -m 'Add some amazing feature'`
4. Push to the branch `git push origin feature/[feature_name]`
5. Open a Pull Request
## License
This project is licensed under the MIT License - see the LICENSE file for details.
## Acknowledgements
- [pdfminer.six](https://github.com/pdfminer/pdfminer.six) for PDF text extraction
- [Hugging Face Transformers](https://github.com/huggingface/transformers) for NLP capabilities
- [JSON Resume](https://jsonresume.org/schema/) for the standardized resume schema