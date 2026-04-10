import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, inject, OnInit, Output, EventEmitter, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { WizardService } from '../../services/wizard-service';
import { Question, Response, Spec } from '../../models/response.model';
import { CONSTANTS } from '../../config/sample-questions';
import { catchError, map, of } from 'rxjs';

@Component({
  selector: 'app-wizard',
  templateUrl: './wizard.html',
  styleUrls: ['./wizard.scss'],
  standalone: true,
  imports: [FormsModule]
})
export class WizardComponent implements OnInit {

  @Output() onComplete = new EventEmitter<any>();

  currentQuestion: Question = { summary: CONSTANTS.REQUIREMENTS_INITIAL_PROMPT, question: "", suggestions: [] };
  answer: string = '';
  sessionId: string = '';
  isLoading = signal(false);
  @ViewChild('textAreaRef') textAreaRef!: ElementRef<HTMLTextAreaElement>;


  wizardService = inject(WizardService);

  constructor() { }

  ngOnInit() {
    this.wizardService.startSession();
    this.wizardService.session$.subscribe((session) => {
      this.sessionId = session?.id || "";
      console.log("Session set to", this.sessionId);
    })
  }

  handleSendMessage() {
    if (!this.answer) return;
    this.isLoading.set(true);
    this.currentQuestion.summary = CONSTANTS.THINKING_TEXT;
    this.currentQuestion.suggestions = [];
    this.currentQuestion.question = "";
    let tempAnswer = this.answer;
    this.answer = "";
    this.wizardService.sendMessage(tempAnswer).pipe(catchError(err => {
      console.log('Error caught:', err);
      return of(null); // fallback value
    }), map((res: Response | null) => {
      console.log("Response received: ", res);
      if (res?.spec?.project_name) {
        return res.spec;
      } else if (res?.reply?.suggestions) {
        res.reply.suggestions = res?.reply.suggestions?.map((suggestion) => {
          return { label: suggestion, selected: false }
        }) || [];
        return res.reply;
      }
      return null;
    })).subscribe((reply: Question | Spec | null) => {
      if((reply as Spec)?.project_name) {
        this.currentQuestion.summary = CONSTANTS.REQUIREMENTS_DONE_TEXT;
        this.currentQuestion.question = CONSTANTS.REQUIREMENTS_DONE_SUBTEXT;
        this.onComplete.emit(reply);
        this.answer = JSON.stringify(reply, null, 2);
        this.textAreaRef.nativeElement.rows = 20;      
      } else {
        this.currentQuestion.summary = (reply as Question)?.summary || CONSTANTS.ERROR_TEXT;
        this.currentQuestion.question = (reply as Question)?.question || "";
        this.currentQuestion.suggestions = (reply as Question)?.suggestions || [];
        this.answer = "";
      }
      this.isLoading.set(false);
    })
  }

  selectSuggestion(suggestion: { label: string, selected: boolean }) {
    this.answer = '';
    suggestion.selected = !suggestion.selected;
    this.currentQuestion?.suggestions?.map(suggestion => {
      if (suggestion.selected) {
        this.answer += suggestion.label + ", ";
      }
    });
    this.answer = this.answer.substring(0, this.answer.length - 2)
  }

  back() {
  }

  complete() {
    // For now, emit a dummy spec. In real implementation, this would be the generated spec from responses.
    const dummySpec = {
      project_name: "Simple To-Do App",
      core_entities: [
        {
          name: "Task",
          attributes: [
            "id: string",
            "title: string",
            "description: string",
            "is_complete: boolean"
          ]
        }
      ],
      functional_requirements: [
        {
          description: "Users can add a new task with a title and a description.",
          name: "Create Task"
        }
      ],
      non_goals: [
        "Team collaboration features."
      ],
      goals: [
        "Enable users to quickly add tasks."
      ],
      non_functional_requirements: {
        performance: "The application should load quickly.",
        scalability: "Not a primary concern.",
        security: "Basic web practices.",
        availability: "Accessible at all times."
      },
      assumptions: [
        "Single-page web application."
      ],
      target_users: [
        "Individuals seeking a personal task management tool"
      ]
    };
    this.onComplete.emit(dummySpec);
  }
}