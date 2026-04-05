import { Component, inject, input, Input, OnInit, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms'; import { MarkdownModule } from 'ngx-markdown';
import { WizardService } from '../requirements/services/wizard-service';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-chatbox',
  standalone: true,
  imports: [FormsModule, MarkdownModule],
  templateUrl: './chatbox.html',
  styleUrl: './chatbox.css'
})
export class ChatboxComponent implements OnInit {

  wizardService = inject(WizardService);
  chatHistory = signal<[{ id: number, text: string, type: string }] | any>([]);
  chatMessage: string = '';
  sendBtnDisabled = signal<boolean>(true);
  sendBtnText = signal<string>("Thinking...");
  @Input() isPreviewMode: boolean = false;

  constructor() { }

  ngOnInit() {
  }

  sendChatMessage() {
    if (this.chatMessage) {
      this.sendBtnDisabled.set(true);
      this.sendBtnText.set("Thinking...");
      this.chatHistory.update((prev) => [...prev, { type: "user", text: this.chatMessage, id: prev.length + 1 }]);
      let tempMessage = this.chatMessage;
      this.chatMessage = '';

      this.wizardService.sendMessage("change").pipe(catchError(err => {
        console.log('Error caught:', err);
        return of(null); // fallback value
      })).subscribe(response => {
        if (response) {
          this.wizardService.sendMessage(tempMessage).pipe(catchError(err => {
            console.log('Error caught:', err);
            return of(null); // fallback value
          })).subscribe(response => {
            if (response) {
              // Update spec based on response
              this.sendBtnDisabled.set(false);
              this.sendBtnText.set("Send");
              console.log('Response received: ' + JSON.stringify(response));
              this.chatHistory.update((prev) => [...prev, { type: "system", text: JSON.stringify(response.reply), id: prev.length + 1 }]);
            }
          });
        }
      });
    }
  }

}