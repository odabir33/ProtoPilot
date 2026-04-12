import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, delay, map, Observable, of } from 'rxjs';
import { Session } from '../models/session.model';
import { Question, Response } from '../models/question.model';
import { CONSTANTS, REQUIREMENTS_QUESTION_FLOW } from '../config/sample-questions';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class WizardService {

  http = inject(HttpClient);

  private sessionSubject:BehaviorSubject<Session | null> = new BehaviorSubject<Session | null>(null);
  session$ = this.sessionSubject.asObservable();

  get session():Session|null {
    return this.sessionSubject.value;
  }

  startSession = ():void => {
    let session: Session = {
      id : crypto.randomUUID()
    }
    this.sessionSubject.next(session);
  }

  sendMessage = (message: string):Observable<Response|null> => {
    if (!this.session) return of(null);
    
    return this.http.post<Response>(CONSTANTS.REQUIREMENTS_AGENT_URL, {
        session_id: this.session.id,
        agent: CONSTANTS.REQUIREMENTS_AGENT_NAME,
        message: message
      });
  }
  
}
