from fpdf import FPDF

class ProjectReportPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'Web-Based Extraction Tool - Semester Project', 0, 0, 'R')
            self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def section_header(self, title):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(44, 62, 80)  # Dark Blue
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(44, 62, 80)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)

    def sub_section_header(self, title):
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(52, 73, 94)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        self.set_font('helvetica', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 7, text)
        self.ln(4)

    def add_bullet(self, text):
        self.set_font('helvetica', '', 11)
        self.set_x(15)
        self.cell(5, 7, '-', 0, 0)
        self.multi_cell(0, 7, text)

def generate_report():
    pdf = ProjectReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # --- Professional Title Page ---
    pdf.add_page()
    # Adding a border to the title page
    pdf.set_line_width(1)
    pdf.rect(10, 10, 190, 277)
    
    pdf.ln(60)
    pdf.set_font('helvetica', 'B', 28)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 20, 'Web-Based Extraction Tool', 0, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font('helvetica', '', 18)
    pdf.set_text_color(127, 140, 141) # Grey
    pdf.cell(0, 10, 'Semester Project', 0, 1, 'C')
    
    pdf.ln(40)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, 'Student Name: HAMMAD AHMAD', 0, 1, 'C')
    pdf.cell(0, 10, 'SAP ID: 63420', 0, 1, 'C')
    
    pdf.ln(20)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, 'Course: Operating Systems', 0, 1, 'C')
    pdf.cell(0, 10, 'Semester: 4', 0, 1, 'C')

    # --- Content Page 1 ---
    pdf.add_page()
    
    pdf.section_header('1. Project Overview')
    pdf.body_text('The Web-Based Extraction Tool is a robust Python application designed to automate the process of gathering information from across the web. It bridges the gap between raw web content and structured analysis, providing a user-friendly interface to scrape, process, and export information without requiring programming expertise.')

    pdf.section_header('2. Problem Statement')
    pdf.body_text('Web content is primarily locked in HTML format, making it difficult for researchers and businesses to analyze efficiently. Manual collection is prone to errors and time-consuming. This project provides a simplified, yet powerful alternative for automated information retrieval.')

    pdf.section_header('3. Core Capabilities')
    
    pdf.sub_section_header('A. Web Scraping Engine')
    pdf.add_bullet('URL-Based Extraction: Fetches content from any publicly accessible URL.')
    pdf.add_bullet('Targeted Selectors: Uses CSS selectors for precise data targeting.')
    pdf.add_bullet('Attribute Mapping: Extracts links, images, and specific HTML metadata.')
    
    pdf.ln(5)
    pdf.sub_section_header('B. Intelligent Navigation')
    pdf.add_bullet('Auto-Pagination: Detects and follows "Next" buttons and page numbers.')
    pdf.add_bullet('Domain Safety: Validates URLs to stay within the target website domain.')
    
    pdf.ln(5)
    pdf.sub_section_header('C. Asynchronous Architecture')
    pdf.add_bullet('Background Processing: Long-running tasks are handled via Celery queues.')
    pdf.add_bullet('Task Isolation: Web interface remains responsive during heavy scraping jobs.')
    pdf.add_bullet('Status Monitoring: Real-time progress tracking for the user.')

    # --- Content Page 2 ---
    pdf.add_page()

    pdf.sub_section_header('D. Export & Clean-up')
    pdf.add_bullet('Automated Cleaning: Removes duplicates and normalizes text content.')
    pdf.add_bullet('Standard Formats: Exports findings into clean CSV files for external analysis.')

    pdf.section_header('4. Technology Stack')
    pdf.sub_section_header('Frontend Interface')
    pdf.body_text('HTML5, CSS3, and JavaScript with AJAX for seamless status updates.')
    
    pdf.sub_section_header('Backend Logic')
    pdf.body_text('Python/Flask (Framework), Celery (Task Queue), and Redis (Message Broker).')
    
    pdf.sub_section_header('Extraction Engine')
    pdf.body_text('BeautifulSoup4 for parsing, Requests for HTTP, and Pandas for processing.')

    pdf.section_header('5. OS Principles & Implementation')
    pdf.add_bullet('Concurrency: Leveraging Celery workers for parallel task execution.')
    pdf.add_bullet('IPC: Redis serves as the communication bridge between separate processes.')
    pdf.add_bullet('System Resources: Implemented rate-limiting to manage network I/O.')

    pdf.section_header('6. Security & Ethics')
    pdf.add_bullet('Politeness Policy: Small delays prevent server overload on target sites.')
    pdf.add_bullet('Public Access: Only scrapes data that is publicly available.')
    pdf.add_bullet('Input Sanitization: Protects the system against malicious URL injections.')

    pdf.section_header('7. Future Development')
    pdf.add_bullet('Database Storage: Permanent persistence of results in SQL/NoSQL.')
    pdf.add_bullet('Dynamic Rendering: Support for JavaScript-heavy sites via Playwright.')
    pdf.add_bullet('Visual UI: Point-and-click interface for element selection.')

    pdf.output('Project_Presentation_Report.pdf')
    print('PDF generated successfully: Project_Presentation_Report.pdf')

if __name__ == "__main__":
    generate_report()
