import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))
from main import process_resumes

class ResumeScreeningUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Resume Screening System")
        self.root.geometry("800x600")
        
        # Create main container
        main_container = ttk.Frame(root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Job Requirements Section
        self.create_job_requirements_section(main_container)
        
        # Results Section
        self.create_results_section(main_container)
        
        # Process Button
        self.process_button = ttk.Button(main_container, text="Process Resumes", command=self.process_resumes)
        self.process_button.grid(row=2, column=0, columnspan=2, pady=10)
        
    def create_job_requirements_section(self, container):
        # Job Requirements Frame
        req_frame = ttk.LabelFrame(container, text="Job Requirements", padding="10")
        req_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Job Description
        ttk.Label(req_frame, text="Job Description:").grid(row=0, column=0, sticky=tk.W)
        self.job_desc = scrolledtext.ScrolledText(req_frame, width=60, height=5)
        self.job_desc.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Required Skills
        ttk.Label(req_frame, text="Required Skills (comma-separated):").grid(row=2, column=0, sticky=tk.W)
        self.skills = ttk.Entry(req_frame, width=60)
        self.skills.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Required Experience
        ttk.Label(req_frame, text="Required Years of Experience:").grid(row=4, column=0, sticky=tk.W)
        self.experience = ttk.Entry(req_frame, width=10)
        self.experience.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Weights
        weights_frame = ttk.Frame(req_frame)
        weights_frame.grid(row=5, column=0, columnspan=2, pady=5)
        
        ttk.Label(weights_frame, text="Weights (should sum to 1.0):").grid(row=0, column=0, columnspan=3)
        
        ttk.Label(weights_frame, text="Skills:").grid(row=1, column=0)
        self.skill_weight = ttk.Entry(weights_frame, width=10)
        self.skill_weight.insert(0, "0.4")
        self.skill_weight.grid(row=1, column=1)
        
        ttk.Label(weights_frame, text="Experience:").grid(row=1, column=2)
        self.exp_weight = ttk.Entry(weights_frame, width=10)
        self.exp_weight.insert(0, "0.3")
        self.exp_weight.grid(row=1, column=3)
        
        ttk.Label(weights_frame, text="Semantic:").grid(row=1, column=4)
        self.semantic_weight = ttk.Entry(weights_frame, width=10)
        self.semantic_weight.insert(0, "0.3")
        self.semantic_weight.grid(row=1, column=5)
        
    def create_results_section(self, container):
        # Results Frame
        results_frame = ttk.LabelFrame(container, text="Results", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, width=70, height=15)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def process_resumes(self):
        # Collect job requirements
        job_requirements = {
            "job_description": self.job_desc.get("1.0", tk.END).strip(),
            "required_skills": [s.strip() for s in self.skills.get().split(",") if s.strip()],
            "required_experience": float(self.experience.get() or 0),
            "skill_weight": float(self.skill_weight.get()),
            "semantic_weight": float(self.semantic_weight.get()),
            "experience_weight": float(self.exp_weight.get())
        }
        
        # Save job requirements
        with open(Path(__file__).parent / "job_requirements.json", "w") as f:
            json.dump(job_requirements, f, indent=4)
        
        # Process resumes
        resumes_dir = Path(__file__).parent.parent / "test_resumes"
        ranked_candidates = process_resumes(job_requirements, resumes_dir)
        
        # Display results
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Ranked Candidates:\n")
        self.results_text.insert(tk.END, "-----------------\n")
        
        for rank, candidate in enumerate(ranked_candidates, 1):
            self.results_text.insert(tk.END, 
                f"{rank}. {candidate['filename']} - Score: {candidate['score']:.2f}\n")
            if 'features' in candidate and 'skills' in candidate['features']:
                self.results_text.insert(tk.END, f"   Matched Skills: {', '.join(candidate['features']['skills'])}\n")
            self.results_text.insert(tk.END, "\n")

def main():
    root = tk.Tk()
    app = ResumeScreeningUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()