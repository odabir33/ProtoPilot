import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WizardComponent } from './features/requirements/components/wizard/wizard';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WizardComponent,],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
}
