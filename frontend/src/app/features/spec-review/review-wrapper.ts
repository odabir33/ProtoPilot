import { Component, inject, Input, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { LeftPanelComponent } from './left-panel';
import { RightPanelComponent } from './right-panel';
import { WizardService } from '../requirements/services/wizard-service';
import { catchError, map, of } from 'rxjs';


@Component({
  selector: 'app-review-wrapper',
  standalone: true,
  imports: [LeftPanelComponent, RightPanelComponent],
  templateUrl: './review-wrapper.html',
  styleUrl: './review-wrapper.css'
})
export class ReviewWrapperComponent implements OnInit {

  @Input() spec: any = {};
  selectedSection: string = '';

  http = inject(HttpClient);
  wizardService = inject(WizardService);

  ngOnInit() {
    if (Object.keys(this.spec).length === 0) {
      this.http.get('/assets/temp_reqs.json').subscribe(data => {
        this.spec = data;
        this.selectedSection = Object.keys(this.spec)[0];
      });
    } else {
      this.selectedSection = Object.keys(this.spec)[0];
    }
  }

  tempReqs = {
  "project_name": "Simple To-Do App",
  "functional_requirements": [
    {
      "description": "Users can add a new task with a title and a description.",
      "name": "Create Task"
    },
    {
      "name": "View Task List",
      "description": "All tasks are displayed in a list."
    },
    {
      "description": "Users can mark a task as completed. Completed tasks should be visually differentiated from active tasks.",
      "name": "Mark Task as Complete"
    }
  ],
  "non_goals": [
    "Team collaboration features.",
    "User accounts and authentication.",
    "Advanced features like sub-tasks, reminders, or attachments."
  ],
  "goals": [
    "Enable users to quickly add tasks.",
    "Allow users to view all their tasks in a list.",
    "Provide a way for users to mark tasks as complete."
  ],
  "non_functional_requirements": {
    "performance": "The application should load quickly and provide instant feedback for user actions.",
    "scalability": "Not a primary concern for a personal task management application.",
    "security": "As a simple client-side application, security will be limited to standard web practices. No sensitive user data is stored.",
    "availability": "The application should be accessible at all times."
  },
  "assumptions": [
    "The application will be a single-page web application.",
    "Task data will be stored in the browser's local storage.",
    "The user interface will be minimalist and intuitive."
  ],
  "target_users": [
    "Individuals seeking a personal task management tool"
  ],
  "open_questions": [
    "Should users be able to edit tasks after creation?",
    "Should users be able to delete tasks?",
    "How should the task list be sorted?"
  ],
  "problem_statement": "Users need a simple and efficient way to manage their personal tasks to stay organized.",
  "constraints": [
    "The application must be built using Java Spring Boot for the backend and Angular for the frontend."
  ]
}

  onSectionSelect(section: string) {
    this.selectedSection = section;
  }

  approveSpec() {
    alert('Specification approved!');
    // Here you could emit an event to the parent or perform other actions
    let message = "Here are the final edited specs: " + JSON.stringify(this.spec);
    this.wizardService.sendMessage(message).pipe(catchError(err => {
          console.log('Error caught:', err);
          return of(null); // fallback value
        })).subscribe((reply) => {
          console.log(reply);
        })
    
  }

}