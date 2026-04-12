import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, inject, OnInit, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { WizardService } from '../../services/wizard-service';
import { Question, Response } from '../../models/question.model';
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
    console.log(this.answer)
    if (!this.answer) return;
    this.isLoading.set(true);
    this.currentQuestion.summary = "Thinking...";
    this.currentQuestion.suggestions = [];
    this.currentQuestion.question = "";
    let tempAnswer = this.answer;
    this.answer = "";
    this.wizardService.sendMessage(tempAnswer).pipe(catchError(err => {
      console.log('Error caught:', err);
      return of(null); // fallback value
    }), map((res: Response | null) => {
      if (res && res.spec) {
        res.spec.suggestions = res?.spec.suggestions?.map((suggestion) => {
          return { label: suggestion, selected: false }
        }) || [];
        return res.spec;
      }
      return null;
    })).subscribe((res: Question | null) => {
      console.log("Summary", res?.summary);
      console.log("Question", res?.question);
      console.log("Suggestions", res?.suggestions);
      if(res?.project_name) {
        this.currentQuestion.summary = "Great! I think we have enough clarity on the idea now!";
        this.currentQuestion.question = "Here are the requirements we discussed in a structured format:"
        this.answer = JSON.stringify(res, null, 2);
        this.textAreaRef.nativeElement.rows = 20;      
      } else {
        this.currentQuestion.summary = res?.summary || "Something went wrong. Please try again! ";
        this.currentQuestion.question = res?.question || "";
        this.currentQuestion.suggestions = res?.suggestions || [];
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
}