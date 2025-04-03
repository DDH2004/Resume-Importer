"""
Resume Importer - Import resume data from LinkedIn profiles or other resume formats
into the resume_data.json format for the Resume Generator.
"""

import os
import re
import json
import argparse
import traceback
from datetime import datetime
import csv
from pathlib import Path

class ResumeImporter:
    """Import resume data from LinkedIn or other formats into a structured JSON format."""

    def __init__(self, debug=False, use_transformers=False):
        """Initialize the resume importer."""
        self.resume_data = self._create_empty_template()
        self.debug = debug
        self.use_transformers = use_transformers
        
        if use_transformers:
            try:
                import transformers
                self.transformers_available = True
                if debug:
                    print(f"Using transformers version: {transformers.__version__}")
            except ImportError:
                self.transformers_available = False
                print("Warning: Transformers library not available. Using regex-only mode.")
        
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
            
            # Post-process the text to improve structure
            processed_text = self._post_process_text(extracted_text)
                
            # Parse the processed text
            self._parse_resume_text(processed_text)
            return True
        except Exception as e:
            import traceback
            print(f"Error processing PDF resume: {e}")
            if self.debug:
                traceback.print_exc()
            return False
    
    def import_from_docx(self, file_path):
        """Import resume data from a Word document."""
        try:
            from docx import Document
            document = Document(file_path)
            
            text = "\n".join([para.text for para in document.paragraphs])
            
            if self.debug:
                print(f"Extracted {len(text)} characters from DOCX")
                
            text = self._post_process_text(text)
            self._parse_resume_text(text)
            return True
        except Exception as e:
            print(f"Error processing DOCX resume: {e}")
            return False
    
    def _post_process_text(self, text):
        """Post-process extracted text to improve structure recognition."""
        # Fix common PDF extraction issues
        
        # 1. Fix merged email addresses
        email_pattern = r'([a-zA-Z0-9_.+-]+)at([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        text = re.sub(email_pattern, r'\1@\2', text)
        
        # 2. Fix line breaks in contact information
        text = re.sub(r'([0-9]{3})[\s\n]+([0-9]{3})[\s\n]+([0-9]{4})', r'\1-\2-\3', text)
        
        # 3. Normalize section headers
        for section in ['EDUCATION', 'EXPERIENCE', 'SKILLS', 'PROJECTS']:
            text = re.sub(rf'{section.lower()}', section.upper(), text, flags=re.IGNORECASE)
        
        # 4. Insert newlines before probable section headers
        text = re.sub(r'([^\n])([A-Z]{5,})', r'\1\n\n\2', text)
        
        return text
    
    def _parse_resume_text(self, text):
        """Parse resume text with improved section detection."""
        if self.debug:
            print("Starting resume parsing...")
        
        # Try transformer-based extraction first if enabled
        if self.use_transformers and hasattr(self, 'transformers_available') and self.transformers_available:
            if self.debug:
                print("Attempting extraction with transformer models")
            
            success = self._extract_with_transformers(text)
            
            if success and self.debug:
                print("Successfully extracted data using transformers")
                return  # Skip the traditional extraction
        
        # Extract basic personal information first (fallback to traditional methods)
        self._extract_personal_info(text)
        self._extract_contact_info(text)
        
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
        
        if not section_matches and self.debug:
            print("No standard sections found. Trying alternative detection methods.")
            # Try with looser patterns if no sections found
            section_matches = list(re.finditer(r'\n([A-Z][A-Z\s]{2,}:?)\s*\n', text))
        
        # Extract sections
        sections = {}
        for i, match in enumerate(section_matches):
            section_name = match.group(1).upper()
            start_idx = match.end()
            end_idx = section_matches[i+1].start() if i+1 < len(section_matches) else len(text)
            section_content = text[start_idx:end_idx].strip()
            sections[section_name] = section_content
            
            if self.debug:
                print(f"Found section: {section_name} ({len(section_content)} chars)")
        
        # Process each section with specialized extractors
        for section_name, content in sections.items():
            if any(work_pattern in section_name for work_pattern in ["WORK", "EXPERIENCE", "EMPLOYMENT", "PROFESSIONAL"]):
                self._extract_work_experience(content)
            elif "EDUCATION" in section_name:
                self._extract_education(content)
            elif "SKILLS" in section_name:
                self._extract_skills(content)
            elif "PROJECT" in section_name:
                self._extract_projects(content)
            elif "CERTIF" in section_name:
                self._extract_certifications(content)
            elif "LANGUAGE" in section_name:
                self._extract_languages(content)
    
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
    
    def _extract_contact_info(self, text):
        """Extract contact information from text."""
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            self.resume_data["basics"]["email"] = email_matches[0]
            if self.debug:
                print(f"Found email: {email_matches[0]}")
        
        # Extract phone number (various formats)
        phone_patterns = [
            r'(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',  # (123) 456-7890 or 123-456-7890
            r'\+\d{1,2}\s\d{3}\s\d{3}\s\d{4}',                       # +1 123 456 7890
            r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}',                    # 123.456.7890
            r'\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}'                       # (123) 456-7890
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, text)
            if phone_matches:
                self.resume_data["basics"]["phone"] = phone_matches[0]
                if self.debug:
                    print(f"Found phone: {phone_matches[0]}")
                break
        
        # Extract LinkedIn URL
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/profile/[\w-]+'
        ]
        
        for pattern in linkedin_patterns:
            linkedin_matches = re.findall(pattern, text, re.IGNORECASE)
            if linkedin_matches:
                url = linkedin_matches[0]
                if not url.startswith('http'):
                    url = f"https://{url}"
                
                self.resume_data["basics"]["profiles"].append({
                    "network": "LinkedIn",
                    "url": url,
                    "username": url.split('/')[-1]
                })
                if self.debug:
                    print(f"Found LinkedIn: {url}")
                break
    
    def _extract_work_experience(self, text):
        """Extract work experience from text."""
        # Split into possible job entries (looking for company or title followed by date)
        job_entries = re.split(r'\n\s*\n', text)
        
        for entry in job_entries:
            if not entry.strip():
                continue
                
            # Look for job title patterns
            title_match = re.search(r'^([A-Z][A-Za-z\s,]+)(?:[-–|]|at|\n)', entry, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else ""
            
            # Look for company name
            company_pattern = r'(?:at|with|for)?\s*([A-Z][A-Za-z0-9\s&,.]+)'
            company_match = re.search(company_pattern, entry[title_match.end() if title_match else 0:])
            company = company_match.group(1).strip() if company_match else ""
            
            # Look for dates (various formats)
            date_patterns = [
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)',
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
            ]
            
            start_date = ""
            end_date = ""
            
            for pattern in date_patterns:
                date_match = re.search(pattern, entry, re.IGNORECASE)
                if date_match:
                    start_date = date_match.group(1)
                    end_date = date_match.group(2)
                    break
            
            # Extract description
            description_match = re.search(rf"{company_pattern}.*?(?=\n\n|\Z)", entry, re.DOTALL)
            description = description_match.group(0).strip() if description_match else ""
            
            # Only add if we have at minimum a title or company
            if title or company:
                work_item = {
                    "name": company,
                    "position": title,
                    "startDate": start_date,
                    "endDate": end_date,
                    "summary": description,
                    "highlights": self._extract_bullet_points(description),
                    "url": "",
                    "keywords": self._extract_keywords_from_text(description)
                }
                
                self.resume_data["work"].append(work_item)
                if self.debug:
                    print(f"Added work: {title} at {company}")
    
    def _extract_education(self, text):
        """Extract education from text."""
        edu_entries = re.split(r'\n\s*\n', text)
        
        for entry in edu_entries:
            if not entry.strip():
                continue
            
            # Look for institution name (universities, colleges)
            institution_patterns = [
                r'([A-Z][A-Za-z\s&,]+(?:University|College|Institute|School))',
                r'((?:University|College|Institute|School)\s+of\s+[A-Z][A-Za-z\s&,]+)'
            ]
            
            institution = ""
            for pattern in institution_patterns:
                inst_match = re.search(pattern, entry)
                if inst_match:
                    institution = inst_match.group(1).strip()
                    break
            
            # Look for degree
            degree_pattern = r'(?:Bachelor|Master|Ph\.?D|Doctor|Associate)(?:\'s|s)?\s+(?:of|in|degree\s+in)?\s+([A-Za-z\s&,]+)'
            degree_match = re.search(degree_pattern, entry, re.IGNORECASE)
            study_type = degree_match.group(0).strip() if degree_match else ""
            area = degree_match.group(1).strip() if degree_match else ""
            
            # Look for dates
            date_patterns = [
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)',
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
            ]
            
            start_date = ""
            end_date = ""
            
            for pattern in date_patterns:
                date_match = re.search(pattern, entry, re.IGNORECASE)
                if date_match:
                    start_date = date_match.group(1)
                    end_date = date_match.group(2)
                    break
            
            # Look for GPA
            gpa_match = re.search(r'GPA:?\s*([\d\.]+)', entry, re.IGNORECASE)
            score = gpa_match.group(1) if gpa_match else ""
            
            if institution or study_type:
                education_item = {
                    "institution": institution,
                    "area": area,
                    "studyType": study_type,
                    "startDate": start_date,
                    "endDate": end_date,
                    "score": score,
                    "courses": self._extract_bullet_points(entry)
                }
                
                self.resume_data["education"].append(education_item)
                if self.debug:
                    print(f"Added education: {study_type} at {institution}")
    
    def _extract_skills(self, text):
        """Extract skills from text."""
        # Look for bullet points or comma-separated skills
        skill_lists = re.findall(r'[•\-*]\s*([^•\-*\n]+)', text)
        if not skill_lists:
            # Try comma-separated
            skill_lists = [text]  # Take the entire section
        
        all_skills = []
        for skill_text in skill_lists:
            # Split by commas or new lines
            skills = [s.strip() for s in re.split(r',|\n', skill_text) if s.strip()]
            all_skills.extend(skills)
        
        # Group skills by category
        skill_categories = {}
        for skill in all_skills:
            category = self._categorize_skill(skill)
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill)
        
        # Create skill entries for each category
        for category, skills in skill_categories.items():
            skill_item = {
                "name": category,
                "level": "",
                "keywords": skills
            }
            self.resume_data["skills"].append(skill_item)
            
            if self.debug:
                print(f"Added skill category: {category} with {len(skills)} skills")
    
    def _extract_projects(self, text):
        """Extract projects from text."""
        # Split into possible project entries
        project_entries = re.split(r'\n\s*\n', text)
        
        for entry in project_entries:
            if not entry.strip():
                continue
            
            # Look for project name/title (usually at the beginning of the entry)
            title_match = re.search(r'^([A-Z][A-Za-z0-9\s&,.:-]+)', entry, re.MULTILINE)
            project_name = title_match.group(1).strip() if title_match else ""
            
            # Look for dates
            date_patterns = [
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)',
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
            ]
            
            start_date = ""
            end_date = ""
            
            for pattern in date_patterns:
                date_match = re.search(pattern, entry, re.IGNORECASE)
                if date_match:
                    start_date = date_match.group(1)
                    end_date = date_match.group(2)
                    break
            
            # Extract description - everything after the title
            description = entry[title_match.end():].strip() if title_match else entry.strip()
            
            # Extract keywords from description
            keywords = self._extract_keywords_from_text(description)
            
            # Extract bullet points (highlights)
            highlights = self._extract_bullet_points(description)
            
            if project_name:
                project_item = {
                    "name": project_name,
                    "description": description,
                    "startDate": start_date,
                    "endDate": end_date,
                    "url": "",
                    "highlights": highlights,
                    "keywords": keywords
                }
                
                self.resume_data["projects"].append(project_item)
                if self.debug:
                    print(f"Added project: {project_name}")
    
    def _extract_certifications(self, text):
        """Extract certifications from text."""
        cert_entries = re.split(r'\n\s*\n', text)
        
        for entry in cert_entries:
            if not entry.strip():
                continue
            
            # Look for certification name
            cert_name = ""
            first_line = entry.split('\n')[0].strip()
            if first_line:
                cert_name = first_line
            
            # Look for issuer
            issuer_match = re.search(r'(?:issued|awarded|certified)\s+by\s+([A-Za-z\s&,.]+)', entry, re.IGNORECASE)
            issuer = issuer_match.group(1).strip() if issuer_match else ""
            
            # Look for date
            date_match = re.search(r'(?:issued|awarded|completed|earned)\s+(?:on|in)\s+(\w+\s+\d{4}|\d{2}/\d{4}|\d{4})', entry, re.IGNORECASE)
            date = date_match.group(1) if date_match else ""
            
            if cert_name:
                cert_item = {
                    "name": cert_name,
                    "date": date,
                    "issuer": issuer,
                    "url": "",
                    "keywords": self._extract_keywords_from_text(entry)
                }
                
                self.resume_data["certificates"].append(cert_item)
                if self.debug:
                    print(f"Added certification: {cert_name}")
    
    def _extract_languages(self, text):
        """Extract language skills from text."""
        # Try to find language entries (usually language name followed by proficiency)
        language_entries = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[:-]?\s*(Native|Fluent|Professional|Intermediate|Basic|Beginner|Advanced)?', text)
        
        for language, fluency in language_entries:
            if language.strip():
                self.resume_data["languages"].append({
                    "language": language.strip(),
                    "fluency": fluency.strip() if fluency else "Fluent"
                })
                
                if self.debug:
                    print(f"Added language: {language}")
    
    def _extract_bullet_points(self, text):
        """Extract bullet points from text."""
        bullet_points = re.findall(r'[•\-*]\s*([^•\-*\n]+)', text)
        return [point.strip() for point in bullet_points if point.strip()]
    
    def _process_education_with_transformers(self, paragraph):
        """Process education information using transformer models."""
        # This would be filled in with actual transformer processing logic
        # For now, extract basic information
        from transformers import pipeline
        
        # Extract education details
        ner = pipeline("ner")
        entities = ner(paragraph)
        
        # Look for educational institution and degree
        institution = ""
        degree = ""
        date = ""
        
        # Process NER results
        # This is a simplified example
        for entity in entities:
            if entity['entity'] == 'I-ORG' and 'university' in entity['word'].lower():
                institution = entity['word']
            elif entity['entity'] == 'I-MISC' and any(d in entity['word'].lower() for d in ['bachelor', 'master', 'phd']):
                degree = entity['word']
            elif entity['entity'] == 'I-DATE':
                date = entity['word']
        
        # Add to resume data if we found meaningful information
        if institution or degree:
            self.resume_data["education"].append({
                "institution": institution,
                "area": "",
                "studyType": degree,
                "startDate": date,
                "endDate": "",
                "score": "",
                "courses": []
            })
    
    def _process_work_with_transformers(self, paragraph):
        """Process work experience using transformer models."""
        # This would be filled in with actual transformer processing logic
        from transformers import pipeline
        
        # Extract work details
        ner = pipeline("ner")
        entities = ner(paragraph)
        
        # Look for company and position
        company = ""
        position = ""
        date = ""
        
        # Process NER results
        # This is a simplified example
        for entity in entities:
            if entity['entity'] == 'I-ORG':
                company = entity['word']
            elif entity['entity'] == 'I-MISC' and any(p in entity['word'].lower() for p in ['engineer', 'manager', 'developer']):
                position = entity['word']
            elif entity['entity'] == 'I-DATE':
                date = entity['word']
        
        # Add to resume data if we found meaningful information
        if company or position:
            self.resume_data["work"].append({
                "name": company,
                "position": position,
                "startDate": date,
                "endDate": "",
                "summary": paragraph,
                "highlights": [],
                "url": "",
                "keywords": []
            })
    
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

    def _extract_with_transformers(self, text):
        """Extract resume information using transformer models."""
        try:
            from transformers import pipeline
            
            if self.debug:
                print("Using transformer models for enhanced extraction")
                
            # 1. Named Entity Recognition for contact info and personal details
            try:
                ner = pipeline("ner")
                entities = ner(text[:1000])  # Process the first 1000 characters for efficiency
                
                # Group entities by type
                grouped_entities = {}
                for entity in entities:
                    if entity['entity'] not in grouped_entities:
                        grouped_entities[entity['entity']] = []
                    grouped_entities[entity['entity']].append(entity)
                
                # Extract person name
                if 'I-PER' in grouped_entities and not self.resume_data["basics"]["name"]:
                    # Logic to reconstruct name from NER tags
                    name_parts = []
                    for entity in grouped_entities['I-PER']:
                        name_parts.append(entity['word'])
                    if name_parts:
                        self.resume_data["basics"]["name"] = " ".join(name_parts)
                        if self.debug:
                            print(f"Found name with NER: {self.resume_data['basics']['name']}")
            except Exception as e:
                if self.debug:
                    print(f"NER processing error: {e}")
                
            # 2. Zero-shot classification for section identification
            try:
                classifier = pipeline("zero-shot-classification")
                
                # Split text into paragraphs
                paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip() and len(p) > 50]
                
                for paragraph in paragraphs:
                    # Identify which section this paragraph belongs to
                    result = classifier(
                        paragraph,
                        candidate_labels=["education", "work experience", "skills", "projects", "personal information"]
                    )
                    
                    section_type = result['labels'][0]  # Get highest probability section
                    confidence = result['scores'][0]    # Get confidence score
                    
                    if confidence > 0.7:  # Only process if confident enough
                        if section_type == "education":
                            self._process_education_with_transformers(paragraph)
                        elif section_type == "work experience":
                            self._process_work_with_transformers(paragraph)
                        # Additional sections could be processed here
            except Exception as e:
                if self.debug:
                    print(f"Classification error: {e}")
                    
            return True
        except ImportError:
            if self.debug:
                print("Transformers library not found, falling back to regex methods")
            return False


def main():
    """Parse command line arguments and import resume data."""
    parser = argparse.ArgumentParser(description='Import resume data from LinkedIn or PDFs.')
    
    parser.add_argument('--input', required=True, help='Path to input file or directory')
    parser.add_argument('--output', default='imported_resume_data.json', help='Output JSON file path')
    parser.add_argument('--format', choices=['linkedin', 'pdf', 'json', 'docx'], default='auto', 
                        help='Format of the input data')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--use-transformers', action='store_true', help='Use transformer models for enhanced extraction')

    args = parser.parse_args()
    
    # Create resume importer with transformer option
    importer = ResumeImporter(debug=args.debug, use_transformers=args.use_transformers)
    
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