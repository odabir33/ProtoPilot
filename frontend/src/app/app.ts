import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WizardComponent } from './features/requirements/components/wizard/wizard';
import { ReviewWrapperComponent } from './features/spec-review/review-wrapper';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WizardComponent, ReviewWrapperComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  currentView: 'wizard' | 'review' = 'wizard';
  spec: any = {};

  onWizardComplete(spec: any) {
    this.spec = spec;
    this.currentView = 'review';
  }
}
