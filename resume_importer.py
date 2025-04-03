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

    def __init__(self):
        """Initialize the resume importer."""
        self.resume_data = self._create_empty_template()
        
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
        """
        Import resume data from a PDF file.
        
        Args:
            file_path: Path to the PDF resume
        """
        try:
            # Check if PyPDF2 is installed
            import PyPDF2
        except ImportError:
            print("Error: PyPDF2 is required for PDF parsing. Install it with: pip install PyPDF2")
            return False
            
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                    
            # Now process the extracted text
            self._parse_resume_text(text)
            return True
            
        except Exception as e:
            print(f"Error processing PDF resume: {e}")
            return False
    
    def _parse_resume_text(self, text):
        """
        Parse resume text and extract structured information.
        
        This is a simplified implementation that will need refinement for production use.
        """
        # Extract name (usually at the top)
        name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text, re.MULTILINE)
        if name_match:
            self.resume_data["basics"]["name"] = name_match.group(1).strip()
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            self.resume_data["basics"]["email"] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
        if phone_match:
            self.resume_data["basics"]["phone"] = phone_match.group(0)
        
        # Extract LinkedIn URL
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        if linkedin_match:
            url = "https://www." + linkedin_match.group(0)
            self.resume_data["basics"]["profiles"].append({
                "network": "LinkedIn",
                "url": url
            })
        
        # Extract sections (this is simplified and will need refinement)
        sections = {}
        current_section = None
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line looks like a section header
            if re.match(r'^[A-Z\s]{4,}$', line):
                current_section = line
                sections[current_section] = []
            elif current_section:
                sections[current_section].append(line)
        
        # Process identified sections
        for section_name, content in sections.items():
            section_text = "\n".join(content)
            
            # Process work experience
            if "EXPERIENCE" in section_name or "WORK" in section_name:
                self._extract_work_experience(section_text)
                
            # Process education
            elif "EDUCATION" in section_name:
                self._extract_education(section_text)
                
            # Process skills
            elif "SKILLS" in section_name:
                self._extract_skills(section_text)
                
            # Process projects
            elif "PROJECT" in section_name:
                self._extract_projects(section_text)
    
    def _extract_work_experience(self, text):
        """Extract work experience from text."""
        # This is a simplified implementation
        # In a production system, you would use more robust NLP methods
        
        # Look for patterns like "Company Name | Job Title | Date Range"
        job_entries = re.findall(r'(.+?)\s*[|│]\s*(.+?)\s*[|│]\s*(.+?)(?:\n|$)', text)
        
        for company, title, date_range in job_entries:
            # Parse date range
            date_match = re.search(r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|Present)', date_range)
            start_date, end_date = "", "Present"
            
            if date_match:
                start_date, end_date = date_match.groups()
            
            # Extract description (simplified)
            description = ""
            company_pattern = re.escape(company)
            description_match = re.search(rf"{company_pattern}.*?(?=\n\n|\Z)", text, re.DOTALL)
            if description_match:
                description = description_match.group(0).replace(company, "", 1).strip()
            
            # Create work item
            work_item = {
                "name": company.strip(),
                "position": title.strip(),
                "startDate": start_date,
                "endDate": end_date,
                "summary": description,
                "highlights": [],
                "url": "",
                "keywords": self._extract_keywords_from_text(description)
            }
            
            # Add bullet points as highlights
            bullet_points = re.findall(r'[•●]\s*(.+?)(?:\n|$)', description)
            if bullet_points:
                work_item["highlights"] = bullet_points
            
            self.resume_data["work"].append(work_item)
    
    def _extract_education(self, text):
        """Extract education information from text."""
        # Look for degree, university, and date patterns
        edu_entries = re.findall(r'((?:Bachelor|Master|Ph.D|Doctor|Associate)\'?s?[^,\n]*),\s*([^,\n]+)(?:,|\n)?\s*(\w+\s+\d{4})?', text)
        
        for degree, institution, graduation_date in edu_entries:
            education_item = {
                "institution": institution.strip(),
                "area": "",  # Might be embedded in degree
                "studyType": degree.strip(),
                "startDate": "",
                "endDate": graduation_date.strip() if graduation_date else "",
                "score": "",
                "courses": []
            }
            
            # Try to extract GPA
            gpa_match = re.search(r'GPA\s*:\s*([\d\.]+)', text)
            if gpa_match:
                education_item["score"] = gpa_match.group(1)
                
            # Try to extract courses
            courses_match = re.search(r'(?:Courses|Coursework):\s*(.*?)(?:\n\n|\Z)', text, re.DOTALL)
            if courses_match:
                course_text = courses_match.group(1)
                education_item["courses"] = [c.strip() for c in re.split(r'[,;]', course_text) if c.strip()]
            
            self.resume_data["education"].append(education_item)
    
    def _extract_skills(self, text):
        """Extract skills from text."""
        # Group skills by category when possible
        skill_groups = {}
        
        # Look for category headers
        category_matches = re.finditer(r'(?:^|\n)([\w\s]+):\s*([\w\s,]+)(?=\n|$)', text)
        
        for match in category_matches:
            category, skills_text = match.groups()
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            skill_groups[category.strip()] = skills
        
        # If no categories found, extract individual skills
        if not skill_groups:
            # Extract individual skills (assuming they're comma or newline separated)
            all_skills = []
            for skill in re.split(r'[,\n]', text):
                skill = skill.strip()
                if skill and not re.match(r'^SKILLS', skill, re.IGNORECASE):
                    all_skills.append(skill)
                    
            if all_skills:
                skill_groups["General Skills"] = all_skills
        
        # Convert to the expected format
        for category, skills in skill_groups.items():
            self.resume_data["skills"].append({
                "name": category,
                "level": "",
                "keywords": skills
            })
    
    def _extract_projects(self, text):
        """Extract projects from text."""
        # Look for project name and potentially a date range
        project_entries = re.findall(r'(?:^|\n)([\w\s\-]+)(?:\s*\|\s*([\w\s\-–]+))?', text)
        
        current_idx = 0
        for project_name, date_range in project_entries:
            project_name = project_name.strip()
            if not project_name or project_name.upper() == "PROJECTS":
                continue
                
            # Find description that follows the project name
            start_idx = text.find(project_name, current_idx)
            if start_idx != -1:
                end_idx = text.find('\n\n', start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                
                description = text[start_idx + len(project_name):end_idx].strip()
                current_idx = end_idx
                
                # Parse date range if available
                start_date, end_date = "", ""
                if date_range:
                    date_match = re.search(r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|Present)', date_range)
                    if date_match:
                        start_date, end_date = date_match.groups()
                
                # Create project item
                project_item = {
                    "name": project_name,
                    "description": description,
                    "startDate": start_date,
                    "endDate": end_date or "Present" if start_date else "",
                    "url": "",
                    "highlights": [],
                    "keywords": self._extract_keywords_from_text(description)
                }
                
                # Extract bullet points as highlights
                bullet_points = re.findall(r'[•●]\s*(.+?)(?:\n|$)', description)
                if bullet_points:
                    project_item["highlights"] = bullet_points
                
                self.resume_data["projects"].append(project_item)
    
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
        """
        Save the resume data to a JSON file.
        
        Args:
            output_file: Path where the resume data will be saved
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.resume_data, f, indent=2)
            print(f"Resume data saved to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False


def main():
    """Parse command line arguments and import resume data."""
    parser = argparse.ArgumentParser(description='Import resume data from LinkedIn or PDFs.')
    
    parser.add_argument('--input', required=True, help='Path to input file or directory')
    parser.add_argument('--output', default='imported_resume_data.json', help='Output JSON file path')
    parser.add_argument('--format', choices=['linkedin', 'pdf', 'json'], default='auto', 
                        help='Format of the input data')
    
    args = parser.parse_args()
    
    # Create resume importer
    importer = ResumeImporter()
    
    # Determine input format if auto
    input_format = args.format
    if input_format == 'auto':
        if os.path.isdir(args.input):
            input_format = 'linkedin'
        elif args.input.lower().endswith('.pdf'):
            input_format = 'pdf'
        elif args.input.lower().endswith('.json'):
            input_format = 'json'
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
    
    if success:
        # Save to output file
        importer.save_to_json(args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())