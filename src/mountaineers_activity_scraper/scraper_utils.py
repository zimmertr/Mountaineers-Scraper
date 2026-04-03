from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, "html.parser")

    def scrape_element_text(self, element, class_name=None, find_child=None, skip_label=False):
        try:
            el = self.soup.find(element, class_=class_name) if class_name else self.soup.find(element)
            if el and find_child:
                el = el.find(find_child)
            if el:
                if skip_label:
                    label = el.find("label")
                    if label:
                        label.decompose()
                return el.get_text(strip=True)
            return ""
        except Exception as e:
            print(f"Failed to scrape {element}.{class_name}: {e}", flush=True)
            return ""

    def scrape_date_range(self):
        try:
            details = self.soup.find("ul", class_="details")
            if details:
                first_li = details.find("li")
                if first_li:
                    text = first_li.get_text(strip=True)
                    text = " ".join(text.split())
                    return text
            return ""
        except Exception as e:
            print(f"Failed to scrape date: {e}", flush=True)
            return ""

    def scrape_primary_leader(self):
        try:
            roster = self.soup.find("div", class_="roster-contact")
            if roster:
                leader_name = ""
                for div in roster.find_all("div"):
                    if "roster" not in div.get("class", []):
                        text = div.get_text(strip=True)
                        if text:
                            leader_name = text
                            break
                position = roster.find("div", class_="roster-position")
                if position:
                    pos_text = position.get_text(strip=True)
                    if leader_name:
                        leader_name = f"{leader_name} ({pos_text})"
                    else:
                        leader_name = pos_text
                leader_name = leader_name.replace("(Primary Leader)", "").strip()
                return leader_name
            return ""
        except Exception as e:
            print(f"Failed to scrape leader: {e}", flush=True)
            return ""

    def scrape_from_ul_details(self, label_text, tag_type="label", extract_tag=None):
        try:
            all_details = self.soup.find_all("ul", class_="details")
            for details in all_details:
                for li in details.find_all("li"):
                    tag = li.find(tag_type)
                    if tag and label_text in tag.get_text():
                        if extract_tag:
                            extracted = li.find(extract_tag)
                            if extracted:
                                text = extracted.get_text(strip=True)
                            else:
                                continue
                        else:
                            text = li.get_text(strip=True)
                            label_text_clean = tag.get_text(strip=True)
                            text = text.replace(label_text_clean, "").strip()
                        if label_text in ["Mileage", "Elevation Gain"]:
                            text = text.replace(" mi", "").replace(" ft", "").strip()
                        return " ".join(text.split())
            return ""
        except Exception as e:
            print(f"Failed to scrape '{label_text}': {e}", flush=True)
            return ""
