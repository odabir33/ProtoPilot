import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WizardComponent } from './features/requirements/components/wizard/wizard';
import { ReviewWrapperComponent } from './features/spec-review/review-wrapper';
import { SpecService } from './features/spec-review/services/spec.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WizardComponent, ReviewWrapperComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  currentView: 'wizard' | 'review' = 'wizard';
  private specService = inject(SpecService);

  onWizardComplete(spec: any) {
    this.specService.setSpec(spec);
    this.currentView = 'review';
  }
}
