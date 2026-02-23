"""
Web scraper for nextleap.app
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests
import yaml
from bs4 import BeautifulSoup

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from utils.db_utils import ensure_dir, save_json
from utils.text_utils import clean_text


class NextLeapScraper:
    """Scraper for nextleap.app website, including structured info."""

    def __init__(self, config_path: str = "config/scraping_config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.target_urls = self.config["target_urls"]
        self.delay = self.config["scraping"]["delay_seconds"]
        self.user_agent = self.config["scraping"].get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        self.headers = {"User-Agent": self.user_agent}

        # Containers for structured data
        self.courses: List[Dict] = []
        self.instructors: List[Dict] = []
        self.faqs: List[Dict] = []
        self.success_stories: List[Dict] = []
        self.perks: List[Dict] = []
        self.other_info: List[Dict] = []

    def _extract_fee(self, text: str) -> str:
        """Heuristic extraction of fee information from nearby text."""
        if "₹" in text or "INR" in text or "Rs" in text:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            fee_lines = [l for l in lines if "₹" in l or "INR" in l or "Rs" in l]
            if fee_lines:
                return fee_lines[0]
        return ""

    def _extract_duration(self, text: str) -> str:
        """Heuristic extraction of duration information from nearby text."""
        patterns = [
            r"\b\d+\s*(weeks?|months?|days?)\b",
            r"\b\d+\s*week(?:s)?\b",
            r"\b\d+\s*month(?:s)?\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return ""

    def _parse_courses(self, soup: BeautifulSoup, url: str) -> None:
        headings = soup.find_all(["h2", "h3", "h4"])
        for h in headings:
            title = h.get_text(strip=True)
            if not title:
                continue
            if "Fellowship" in title or "Course" in title or "Program" in title:
                parent_text = h.find_parent().get_text(separator="\n", strip=True)
                fee = self._extract_fee(parent_text)
                duration = self._extract_duration(parent_text)

                course = {
                    "name": title,
                    "short_description": "",
                    "fee_structure": fee or None,
                    "duration": duration or None,
                    "instructors": [],
                    "url": url,
                }
                if course not in self.courses:
                    self.courses.append(course)

    def _parse_faqs(self, soup: BeautifulSoup, url: str) -> None:
        faq_keywords = ["faq", "questions", "frequently asked"]
        possible_sections = []
        for section in soup.find_all(["section", "div", "details"]):
            section_text = section.get_text(separator=" ", strip=True).lower()
            if any(k in section_text for k in faq_keywords):
                possible_sections.append(section)

        for section in possible_sections:
            for details in section.find_all("details"):
                q_el = details.find(["summary", "h3", "h4"])
                a_el = details
                if not q_el:
                    continue
                question = q_el.get_text(strip=True)
                answer = a_el.get_text(separator="\n", strip=True)
                if not question or not answer:
                    continue
                self.faqs.append(
                    {
                        "question": question,
                        "answer": answer,
                        "category": None,
                        "source_url": url,
                    }
                )

    def _parse_success_stories(self, soup: BeautifulSoup, url: str) -> None:
        cards = soup.find_all("article")
        if not cards:
            cards = soup.find_all("div", class_=re.compile("card|testimonial", re.I))

        for card in cards:
            text = card.get_text(separator="\n", strip=True)
            if not text:
                continue
            if any(k in text.lower() for k in ["review", "testimonial", "journey"]):
                name_el = card.find(["h3", "h4", "strong"])
                name = name_el.get_text(strip=True) if name_el else None
                self.success_stories.append(
                    {
                        "student_name": name,
                        "testimonial_text": text,
                        "course": None,
                        "company": None,
                        "previous_role": None,
                        "new_role": None,
                        "source_url": url,
                    }
                )

    def _parse_perks(self, soup: BeautifulSoup, url: str) -> None:
        bullet_lists = soup.find_all(["ul", "ol"])
        for ul in bullet_lists:
            items = [li.get_text(strip=True) for li in ul.find_all("li")]
            for item in items:
                lower = item.lower()
                if any(
                    k in lower
                    for k in [
                        "mentorship",
                        "placement",
                        "job",
                        "career",
                        "community",
                        "projects",
                        "portfolio",
                        "mock interview",
                        "live",
                        "cohort",
                    ]
                ):
                    self.perks.append({"description": item, "source_url": url})

    def _parse_course_detail(self, soup: BeautifulSoup, url: str) -> None:
        """Extract detailed information from a specific course page using JSON payload or heuristics."""
        # Try finding Next.js data first
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        course_data = {}
        
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                page_props = data.get("props", {}).get("pageProps", {})
                course_detail = page_props.get("course", {})
                
                if course_detail:
                    # Extract from JSON
                    course_name = course_detail.get("title", "")
                    price_info = course_detail.get("price", {})
                    fee = f"₹{price_info.get('sellingPrice', '')}"
                    original_fee = f"₹{price_info.get('mrp', '')}"
                    duration = course_detail.get("duration", "")
                    
                    # Instructors
                    instructors = []
                    for inst in course_detail.get("instructors", []):
                        instructors.append(f"{inst.get('name', '')} ({inst.get('designation', '')})")
                    
                    # Placement
                    placement = course_detail.get("careerAssistance", "Detailed support provided.")
                    if not placement or placement == "Detailed support provided.":
                         # Heuristic if empty
                         placement = "Placement support/Career assistance included."
                    
                    # Start Date
                    start_date = course_detail.get("nextCohortDate", "")
                    if not start_date:
                        # Try looking into cohort structure if exists
                        cohorts = course_detail.get("cohorts", [])
                        if cohorts:
                            start_date = cohorts[0].get("startDate", "")
                    
                    # Curriculum
                    curriculum = []
                    for module in course_detail.get("curriculum", []):
                        curriculum.append(f"- {module.get('title', '')}")
                    curriculum_text = "\n".join(curriculum)

                    course_data = {
                        "name": course_name,
                        "url": url,
                        "fee": fee if fee != "₹" else "Check website",
                        "original_fee": original_fee if original_fee != "₹" else "Check website",
                        "duration": duration or "Check website",
                        "start_date": start_date or "Check website",
                        "instructors": instructors,
                        "placement_support": placement,
                        "curriculum": curriculum_text or "Details on website",
                        "discounts": f"Discounted from {original_fee}" if original_fee != "₹" else "No specific discounts found",
                        "status": "extracted_via_json"
                    }
            except Exception as e:
                print(f"Error parsing JSON for {url}: {e}")

        # Fallback to heuristics if JSON extraction failed or partial
        if not course_data:
            content = soup.get_text(separator="\n", strip=True)
            title_el = soup.find("h1")
            course_name = title_el.get_text(strip=True) if title_el else url.split("/")[-1].replace("-", " ").title()
            
            course_data = {
                "name": course_name,
                "url": url,
                "fee": self._extract_fee(content) or "Check website",
                "duration": self._extract_duration(content) or "Check website",
                "start_date": "Check website",
                "instructors": [],
                "placement_support": "Placement support mentioned" if "placement" in content.lower() else "Check website",
                "discounts": self._extract_discounts(content),
                "curriculum": "Details on website",
                "status": "extracted_via_heuristics"
            }

        # Build a rich content string for RAG
        rich_content = f"""
Course: {course_data['name']}
URL: {course_data['url']}
Fee: {course_data['fee']} (Original: {course_data.get('original_fee', 'N/A')})
Duration: {course_data['duration']}
Next Batch Starts: {course_data['start_date']}
Mentors/Instructors: {', '.join(course_data['instructors'])}
Placement Support: {course_data['placement_support']}
Discounts: {course_data['discounts']}
Curriculum:
{course_data.get('curriculum', 'See website for details')}
"""
        course_data["full_extracted_content"] = rich_content
        
        # Update or add to courses
        existing = next((c for c in self.courses if c["url"] == url), None)
        if existing:
            existing.update(course_data)
        else:
            self.courses.append(course_data)

    def _extract_discounts(self, text: str) -> str:
        """Heuristic extraction of discount info."""
        patterns = [r"\b\d+%\s+off\b", r"early\s+bird\b", r"discount\s+of\s+₹\d+"]
        found = []
        for pat in patterns:
            m = re.findall(pat, text, re.I)
            if m:
                found.extend(m)
        return ", ".join(found) if found else "No specific discounts found"

    def _parse_other_info(self, soup: BeautifulSoup, url: str) -> None:
        body = soup.find("body")
        if not body:
            return
        text = body.get_text(separator="\n", strip=True)
        self.other_info.append({"url": url, "content": text})

    def scrape_page(self, url: str) -> Dict[str, str]:
        """
        Scrape a single page and populate both raw and structured data.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text()
            text = clean_text(text)

            title = soup.find("title")
            title_text = title.get_text() if title else url

            normalized_url = url.rstrip("/")
            if normalized_url in ("https://nextleap.app", "https://nextleap.app/"):
                self._parse_courses(soup, url)
                self._parse_perks(soup, url)
                self._parse_other_info(soup, url)
            elif "/course/" in normalized_url:
                self._parse_course_detail(soup, url)
                self._parse_other_info(soup, url)
            elif "/reviews" in normalized_url:
                self._parse_success_stories(soup, url)
                self._parse_other_info(soup, url)
            elif "faq" in normalized_url or "questions" in normalized_url:
                self._parse_faqs(soup, url)
                self._parse_other_info(soup, url)
            else:
                self._parse_other_info(soup, url)

            # If it's a course page, use the rich content we built
            final_content = text
            if "/course/" in url:
                course_match = next((c for c in self.courses if c["url"] == url), None)
                if course_match:
                    final_content = course_match["full_extracted_content"]

            return {
                "url": url,
                "title": title_text,
                "content": final_content,
                "status": "success",
            }
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {
                "url": url,
                "title": "",
                "content": "",
                "status": "error",
                "error": str(e),
            }

    def scrape_all(self) -> List[Dict[str, str]]:
        """
        Scrape all target URLs and build both raw and structured datasets.
        """
        results: List[Dict[str, str]] = []

        for url in self.target_urls:
            print(f"Scraping: {url}")
            result = self.scrape_page(url)
            results.append(result)
            time.sleep(self.delay)

        return results

    def save_raw_data(self, data: List[Dict[str, str]], output_dir: str = None):
        if output_dir is None:
            output_dir = self.config["output"]["raw_data_dir"]

        ensure_dir(output_dir)
        output_path = Path(output_dir) / "raw_scraped_data.json"
        save_json(data, str(output_path))
        print(f"Saved raw data to {output_path}")

    def save_structured_data(self, output_dir: str = None):
        """
        Save structured, field-level information useful for Q&A.
        """
        if output_dir is None:
            output_dir = self.config["output"].get(
                "processed_data_dir", "./data/processed"
            )

        ensure_dir(output_dir)
        structured = {
            "courses": self.courses,
            "instructors": self.instructors,
            "faqs": self.faqs,
            "success_stories": self.success_stories,
            "perks": self.perks,
            "other_info": self.other_info,
        }
        output_path = Path(output_dir) / "structured_nextleap_info.json"
        save_json(structured, str(output_path))
        print(f"Saved structured data to {output_path}")


if __name__ == "__main__":
    scraper = NextLeapScraper()
    scraped_data = scraper.scrape_all()
    scraper.save_raw_data(scraped_data)
    scraper.save_structured_data()
