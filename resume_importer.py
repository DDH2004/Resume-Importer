"""
Resume Importer - Import resume data from LinkedIn profiles or other resume formats
into the resume_data.json format for the Resume Generator.
"""

import os
import re
import json
import argparse
from datetime import datetime
import csv
from pathlib import Path

class ResumeImporter:
    """Import resume data from LinkedIn or other formats into a structured JSON format."""

    def __init__(self, debug=False):
        """Initialize the resume importer."""
        self.resume_data = self._create_empty_template()
        self.debug = debug
        
    def _create_empty_template(self):
        """Create an empty resume data template."""
        return {
            "basics": {
                "name": "",
                "label": "",
                "image": "",
                "email": "",
                "phone": "",
                "url": "",
                "summary": "",
                "location": {
                    "address": "",
                    "postalCode": "",
                    "city": "",
                    "countryCode": "",
                    "region": ""
                },
                "profiles": []
            },
            "work": [],
            "volunteer": [],
            "education": [],
            "awards": [],
            "certificates": [],
            "publications": [],
            "skills": [],
            "languages": [],
            "interests": [],
            "references": [],
            "projects": []
        }
    
    def import_from_linkedin_export(self, file_path):
        """
        Import resume data from a LinkedIn data export (CSV files).
        
        Args:
            file_path: Path to the LinkedIn data export zip file or directory
        """
        input_path = Path(file_path)
        
        # If it's a directory, look for CSV files
        if input_path.is_dir():
            self._process_linkedin_directory(input_path)
        else:
            print(f"Error: {file_path} is not a directory. Please provide the path to the LinkedIn export directory.")
            return False
            
        return True
        
    def _process_linkedin_directory(self, directory_path):
        """Process LinkedIn data export directory containing CSV files."""
        # Map of expected filenames to processing functions
        file_processors = {
            "Profile.csv": self._process_linkedin_profile,
            "Positions.csv": self._process_linkedin_positions,
            "Education.csv": self._process_linkedin_education,
            "Skills.csv": self._process_linkedin_skills,
            "Languages.csv": self._process_linkedin_languages,
            "Projects.csv": self._process_linkedin_projects,
            "Certifications.csv": self._process_linkedin_certifications
        }
        
        # Process each file if it exists
        for filename, processor in file_processors.items():
            file_path = directory_path / filename
            if file_path.exists():
                processor(file_path)
            else:
                print(f"Warning: {filename} not found in the LinkedIn export directory.")
    
    def _process_linkedin_profile(self, file_path):
        """Process LinkedIn profile data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Basic information
                    self.resume_data["basics"]["name"] = row.get("First Name", "") + " " + row.get("Last Name", "")
                    self.resume_data["basics"]["label"] = row.get("Headline", "")
                    self.resume_data["basics"]["summary"] = row.get("Summary", "")
                    
                    # Location
                    self.resume_data["basics"]["location"]["city"] = row.get("City", "")
                    self.resume_data["basics"]["location"]["region"] = row.get("State", "")
                    self.resume_data["basics"]["location"]["countryCode"] = row.get("Country", "")
                    
                    # Add LinkedIn profile
                    self.resume_data["basics"]["profiles"].append({
                        "network": "LinkedIn",
                        "url": row.get("Public Profile Url", ""),
                        "username": row.get("Vanity Name", "")
                    })
                    
                    # Only process first row as there should only be one profile
                    break
        except Exception as e:
            print(f"Error processing LinkedIn profile: {e}")
    
    def _process_linkedin_positions(self, file_path):
        """Process LinkedIn work positions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    work_item = {
                        "name": row.get("Company Name", ""),
                        "position": row.get("Title", ""),
                        "startDate": self._format_linkedin_date(row.get("Started On", "")),
                        "endDate": self._format_linkedin_date(row.get("Finished On", "")) or "Present",
                        "summary": row.get("Description", ""),
                        "highlights": [],
                        "url": "",
                        "keywords": self._extract_keywords_from_text(row.get("Description", ""))
                    }
                    
                    # Add the work experience
                    self.resume_data["work"].append(work_item)
        except Exception as e:
            print(f"Error processing LinkedIn positions: {e}")
    
    def _process_linkedin_education(self, file_path):
        """Process LinkedIn education data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    education_item = {
                        "institution": row.get("School Name", ""),
                        "area": row.get("Field Of Study", ""),
                        "studyType": row.get("Degree Name", ""),
                        "startDate": self._format_linkedin_date(row.get("Start Date", "")),
                        "endDate": self._format_linkedin_date(row.get("End Date", "")) or "Present",
                        "score": "",
                        "courses": [course.strip() for course in row.get("Activities and Societies", "").split(",") if course.strip()]
                    }
                    
                    # Add the education
                    self.resume_data["education"].append(education_item)
        except Exception as e:
            print(f"Error processing LinkedIn education: {e}")
    
    def _process_linkedin_skills(self, file_path):
        """Process LinkedIn skills data."""
        try:
            # Group skills by category
            skill_categories = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    skill_name = row.get("Name", "")
                    if not skill_name:
                        continue
                        
                    # Try to categorize the skill
                    category = self._categorize_skill(skill_name)
                    
                    if category not in skill_categories:
                        skill_categories[category] = []
                    
                    skill_categories[category].append(skill_name)
            
            # Create skill entries for each category
            for category, skills in skill_categories.items():
                skill_item = {
                    "name": category,
                    "level": "",
                    "keywords": skills
                }
                self.resume_data["skills"].append(skill_item)
                
        except Exception as e:
            print(f"Error processing LinkedIn skills: {e}")
    
    def _process_linkedin_languages(self, file_path):
        """Process LinkedIn languages data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    language_item = {
                        "language": row.get("Name", ""),
                        "fluency": row.get("Proficiency", "")
                    }
                    
                    # Add the language
                    self.resume_data["languages"].append(language_item)
        except Exception as e:
            print(f"Error processing LinkedIn languages: {e}")
    
    def _process_linkedin_projects(self, file_path):
        """Process LinkedIn projects data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    project_item = {
                        "name": row.get("Title", ""),
                        "description": row.get("Description", ""),
                        "startDate": self._format_linkedin_date(row.get("Started On", "")),
                        "endDate": self._format_linkedin_date(row.get("Finished On", "")) or "Present",
                        "url": row.get("Url", ""),
                        "highlights": [],
                        "keywords": self._extract_keywords_from_text(row.get("Description", ""))
                    }
                    
                    # Add the project
                    self.resume_data["projects"].append(project_item)
        except Exception as e:
            print(f"Error processing LinkedIn projects: {e}")
    
    def _process_linkedin_certifications(self, file_path):
        """Process LinkedIn certifications data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cert_item = {
                        "name": row.get("Name", ""),
                        "date": self._format_linkedin_date(row.get("Started On", "")),
                        "issuer": row.get("Authority", ""),
                        "url": row.get("Url", ""),
                        "keywords": []
                    }
                    
                    # Add the certification
                    self.resume_data["certificates"].append(cert_item)
        except Exception as e:
            print(f"Error processing LinkedIn certifications: {e}")
    
    def _format_linkedin_date(self, date_str):
        """Format LinkedIn date string to YYYY-MM-DD or YYYY-MM format."""
        if not date_str:
            return ""
            
        # LinkedIn date format is typically MM/DD/YYYY or MM/YYYY
        parts = date_str.split('/')
        
        if len(parts) == 3:  # MM/DD/YYYY
            month, day, year = parts
            return f"{year}-{month}"
        elif len(parts) == 2:  # MM/YYYY
            month, year = parts
            return f"{year}-{month}"
        else:
            return date_str  # Return as-is if format is unknown
    
    def _extract_keywords_from_text(self, text):
        """Extract potential keywords from text."""
        if not text:
            return []
            
        # Common technical keywords to look for
        tech_patterns = [
            r'python|java|javascript|typescript|html|css|c\+\+|ruby|php|swift|kotlin|go|rust|scala|sql',
            r'react|angular|vue|node|express|django|flask|spring|laravel|rails',
            r'aws|azure|gcp|docker|kubernetes|terraform|jenkins|git|ci/cd',
            r'machine learning|ml|ai|data science|nlp|computer vision',
            r'agile|scrum|kanban|waterfall|leadership|teamwork|communication'
        ]
        
        keywords = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text.lower())
            keywords.extend(matches)
            
        return list(set(keywords))  # Remove duplicates
    
    def _categorize_skill(self, skill_name):
        """Categorize a skill into a group."""
        skill_lower = skill_name.lower()
        
        # Define categories and their keywords
        categories = {
            "Programming Languages": ["python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust", "scala"],
            "Web Development": ["html", "css", "react", "angular", "vue", "node", "express", "django", "flask"],
            "Data Science": ["machine learning", "data analysis", "statistics", "jupyter", "pandas", "numpy", "tensorflow", "pytorch", "ai"],
            "DevOps & Cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform"],
            "Databases": ["sql", "nosql", "mongodb", "postgresql", "mysql", "firebase", "redis"],
            "Mobile Development": ["android", "ios", "flutter", "react native", "swift", "kotlin"],
            "Soft Skills": ["leadership", "teamwork", "communication", "problem solving", "project management"]
        }
        
        # Check which category the skill belongs to
        for category, keywords in categories.items():
            if any(keyword in skill_lower for keyword in keywords):
                return category
        
        # Default category
        return "Other Skills"
    
    def import_from_pdf(self, file_path):
        try:
            # Try multiple PDF extraction libraries for better results
            extracted_text = None
            
            # Option 1: Try pdfminer.six (best structure preservation)
            try:
                from pdfminer.high_level import extract_text
                extracted_text = extract_text(file_path)
                if self.debug:
                    print("Successfully used pdfminer.six")
            except ImportError:
                pass
                
            # Option 2: Try pytesseract if text extraction is poor
            if not extracted_text or len(extracted_text.strip()) < 100:
                try:
                    import pytesseract
                    from pdf2image import convert_from_path
                    if self.debug:
                        print("Falling back to OCR with pytesseract")
                    images = convert_from_path(file_path)
                    extracted_text = ""
                    for img in images:
                        extracted_text += pytesseract.image_to_string(img)
                except ImportError:
                    pass
                    
            # Option 3: Fallback to PyPDF2
            if not extracted_text:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    extracted_text = ""
                    for page in reader.pages:
                        extracted_text += page.extract_text()
                if self.debug:
                    print("Used PyPDF2 as fallback")
                        
            if self.debug:
                print(f"Extracted {len(extracted_text)} characters of text")
                print("------ Extracted Text Preview ------")
                print(extracted_text[:500])
                print("-----------------------------------")
                
            self._parse_resume_text(extracted_text)
            return True
        except Exception as e:
            print(f"Error processing PDF resume: {e}")
            return False
    
    def import_from_docx(self, file_path):
        """Import resume data from a Word document."""
        try:
            from docx import Document
            document = Document(file_path)
            
            text = "\n".join([para.text for para in document.paragraphs])
            
            if self.debug:
                print(f"Extracted {len(text)} characters from DOCX")
                
            self._parse_resume_text(text)
            return True
        except Exception as e:
            print(f"Error processing DOCX resume: {e}")
            return False
    
    def _parse_resume_text(self, text):
        """Parse resume text with improved section detection."""
        if self.debug:
            print("Starting resume parsing...")
        
        # Common section headers in resumes
        section_patterns = [
            r'(WORK|PROFESSIONAL|EMPLOYMENT)\s?(EXPERIENCE|HISTORY)',
            r'EDUCATION',
            r'SKILLS',
            r'PROJECTS?',
            r'CERTIFICATIONS?',
            r'LANGUAGES?',
            r'(VOLUNTEER|COMMUNITY)\s?(EXPERIENCE|WORK|SERVICE)',
            r'PUBLICATIONS?',
            r'AWARDS',
            r'INTERESTS'
        ]
        
        # Combine patterns for section detection
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        
        # Find potential section boundaries
        section_matches = list(re.finditer(rf'(?:^|\n)({combined_pattern})(?::|\n|$)', text, re.IGNORECASE))
        
        # Extract sections
        sections = {}
        for i, match in enumerate(section_matches):
            section_name = match.group(1).upper()
            start_idx = match.end()
            end_idx = section_matches[i+1].start() if i+1 < len(section_matches) else len(text)
            section_content = text[start_idx:end_idx].strip()
            sections[section_name] = section_content
            
            if self.debug:
                print(f"Processing section: {section_name}")
                print(f"Found {len(self.resume_data['work'])} work experiences")
                print(f"Found {len(self.resume_data['education'])} education entries")
                print(f"Found {len(self.resume_data['skills'])} skill categories")
        
        # Process each section with specialized extractors
        # Continue with existing section processing...
    
    def _extract_personal_info(self, text):
        """Extract personal information with improved name detection."""
        # Try multiple name detection approaches
        
        # Approach 1: First few lines, looking for name-like patterns
        first_lines = text.strip().split('\n')[:7]
        for line in first_lines:
            line = line.strip()
            # More flexible name pattern (2-4 words, each capitalized)
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$', line) and len(line) < 40:
                self.resume_data["basics"]["name"] = line
                if self.debug:
                    print(f"Found name (pattern match): {line}")
                break
                
        # Approach 2: Look for common name prefix patterns
        if not self.resume_data["basics"]["name"]:
            name_match = re.search(r'(?:Name|NAME):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text)
            if name_match:
                self.resume_data["basics"]["name"] = name_match.group(1)
                if self.debug:
                    print(f"Found name (prefix match): {name_match.group(1)}")
    
    def load_from_json(self, file_path):
        """
        Load resume data from an existing JSON file.
        
        Args:
            file_path: Path to the JSON file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.resume_data = data
            return True
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return False
    
    def save_to_json(self, output_file):
        """Save the resume data with confidence scores."""
        # Calculate confidence based on how many fields were populated
        confidence = self._calculate_confidence()
        
        # Add metadata to the output
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "confidence_score": confidence,
                "fields_extracted": self._count_populated_fields()
            },
            "resume_data": self.resume_data
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Resume data saved to {output_file} (confidence: {confidence:.2f})")
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False
    
    def _calculate_confidence(self):
        """Calculate confidence score based on populated fields."""
        populated_fields = self._count_populated_fields()
        total_fields = sum(len(section) for section in self.resume_data.values() if isinstance(section, list))
        return (populated_fields / total_fields) * 100 if total_fields > 0 else 0
    
    def _count_populated_fields(self):
        """Count the number of populated fields in the resume data."""
        count = 0
        for section in self.resume_data.values():
            if isinstance(section, list):
                count += len(section)
            elif isinstance(section, dict):
                count += sum(1 for value in section.values() if value)
        return count


def main():
    """Parse command line arguments and import resume data."""
    parser = argparse.ArgumentParser(description='Import resume data from LinkedIn or PDFs.')
    
    parser.add_argument('--input', required=True, help='Path to input file or directory')
    parser.add_argument('--output', default='imported_resume_data.json', help='Output JSON file path')
    parser.add_argument('--format', choices=['linkedin', 'pdf', 'json', 'docx'], default='auto', 
                        help='Format of the input data')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()
    
    # Create resume importer
    importer = ResumeImporter(debug=args.debug)
    
    # Determine input format if auto
    input_format = args.format
    if input_format == 'auto':
        if os.path.isdir(args.input):
            input_format = 'linkedin'
        elif args.input.lower().endswith('.pdf'):
            input_format = 'pdf'
        elif args.input.lower().endswith('.json'):
            input_format = 'json'
        elif args.input.lower().endswith('.docx'):
            input_format = 'docx'
        else:
            print("Error: Could not determine input format. Please specify with --format.")
            return 1
    
    # Process based on input format
    success = False
    if input_format == 'linkedin':
        success = importer.import_from_linkedin_export(args.input)
    elif input_format == 'pdf':
        success = importer.import_from_pdf(args.input)
    elif input_format == 'json':
        success = importer.load_from_json(args.input)
    elif input_format == 'docx':
        success = importer.import_from_docx(args.input)
    
    if success:
        # Save to output file
        importer.save_to_json(args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())