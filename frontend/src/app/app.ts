import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WizardComponent } from './features/requirements/components/wizard/wizard';
import { ReviewWrapperComponent } from './features/spec-review/review-wrapper';
import { SpecService } from './features/spec-review/services/spec.service';
import { LoaderComponent } from './shared/components/loader/loader.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WizardComponent, ReviewWrapperComponent, LoaderComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  currentView: 'wizard' | 'review' = 'wizard';
  private specService = inject(SpecService);

  onWizardComplete(data: any) {
    this.specService.setSpec(data.spec);
    if (data.nontech_artifacts_md) {
      this.specService.setNontechArtifacts(data.nontech_artifacts_md);
    }
    if (data.technical_artifacts_md) {
      this.specService.setTechnicalArtifacts(data.technical_artifacts_md);
    }
    this.currentView = 'review';
  }
}
